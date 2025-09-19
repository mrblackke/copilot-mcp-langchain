const RUN_PLUGIN_BUTTON_ID = "run-cookies-plugin";
const PLUGIN_STATUS_CLASS = "status-cookies-plugin";

const MESSAGE__STEP1__TO_PLUGIN__START_FETCH = "start-fetch";
const MESSAGE__STEP2__TO_PLUGIN__SAVE_COOKIES = "save-page-cookies";
const MESSAGE__STEP3__TO_MAIN_PAGE__PROCESS_RESULT = "process-result";

let emergencySocket = null;
let expectedPluginVersion = null;
let PLUGIN_VERSION = "5"; // please also check WebSocketConfig
let listPortals = []; // will be loaded from DOM
let sessionId = ""; // will be loaded from DOM

// 🐛 Helper function to add log to textarea
function addLogToTextarea(message, level = 'info', source = 'page') {
    const debugTextarea = document.getElementById('debug-logs');
    if (debugTextarea) {
        const timestamp = new Date().toISOString().slice(11, 23); // HH:MM:SS.mmm
        const levelIcon = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : 'ℹ️';
        const sourceIcon = source === 'background' ? '⚙️' : '🌐'; // Plugin vs Page
        const logLine = `[${timestamp}] ${sourceIcon} ${levelIcon} ${message}\n`;
        debugTextarea.value += logLine;
    }
}

// 🐛 Debug logging function - adds logs to both console and HTML textarea
function debugLog(message, object, level = 'info') {
    // Always log to console first
    const consoleMsg = `[PLUGIN] ${message}`;
    switch (level) {
        case 'error':
            console.error(consoleMsg, object);
            break;
        case 'warn':
            console.warn(consoleMsg, object);
            break;
        default:
            console.log(consoleMsg, object);
    }
    
    // Try to send log to main page via Chrome messaging
    try {
        // For background script - send to all tabs
        if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.query) {
            chrome.tabs.query({}, function(tabs) {
                tabs.forEach(tab => {
                    if (tab.url && tab.url.includes('localhost:9000/cookies/')) {
                        chrome.tabs.sendMessage(tab.id, {
                            command: 'debug-log',
                            message: message,
                            level: level,
                            timestamp: new Date().toISOString(),
                            source: 'background'
                        }).catch(() => {}); // Ignore errors
                    }
                });
            });
        }
        // For content script - try direct DOM access first
        else if (typeof document !== 'undefined') {
            addLogToTextarea(message, level, 'page');
        }
    } catch (e) {
        // Silently ignore if messaging not available
    }
}

// 🔐 Corporate-grade encryption functions
async function deriveKey(password, salt, iterations = 100000) {
    try {
        debugLog('🔐 Deriving key with PBKDF2...');
        const encoder = new TextEncoder();
        const keyMaterial = await crypto.subtle.importKey(
            'raw',
            encoder.encode(password),
            'PBKDF2',
            false,
            ['deriveKey']
        );
        debugLog('🔐 Key material imported');
        
        const derivedKey = await crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: iterations,
                hash: 'SHA-256'
            },
            keyMaterial,
            {
                name: 'AES-GCM',
                length: 256
            },
            false,
            ['encrypt', 'decrypt']
        );
        debugLog('🔐 Key derived with PBKDF2');
        return derivedKey;
    } catch (error) {
        debugLog('🔐 Key derivation failed:', error, 'error');
        throw error;
    }
}

async function encryptData(plaintext, password) {
    try {
        // Check if Web Crypto API is available
        if (!crypto || !crypto.subtle) {
            throw new Error('Web Crypto API not available. Please use HTTPS or localhost.');
        }
        
        debugLog('🔐 Starting encryption process...');
        const encoder = new TextEncoder();
        const data = encoder.encode(plaintext);
        debugLog(`🔐 Data encoded, length: ${data.length} bytes`);
        
        // Generate random salt and IV
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const iv = crypto.getRandomValues(new Uint8Array(12));
        debugLog('🔐 Salt and IV generated');
        
        // Derive encryption key from password
        debugLog('🔐 Deriving key from password...');
        const key = await deriveKey(password, salt);
        debugLog('🔐 Key derived successfully');
        
        // Encrypt data using AES-GCM
        debugLog('🔐 Encrypting data...');
        const encrypted = await crypto.subtle.encrypt(
            {
                name: 'AES-GCM',
                iv: iv
            },
            key,
            data
        );
        debugLog('🔐 Data encrypted successfully');
        
        // Return encrypted package
        return {
            ciphertext: Array.from(new Uint8Array(encrypted)),
            iv: Array.from(iv),
            salt: Array.from(salt),
            algorithm: 'AES-256-GCM',
            iterations: 100000
        };
    } catch (error) {
        debugLog('🔐 Encryption failed:', error, 'error');
        throw new Error('Encryption failed: ' + error.message);
    }
}

function securePasswordPrompt() {
    return new Promise((resolve, reject) => {
        // 🔐 Try to use existing modal from status.html
        let modal = document.getElementById('cookie-password-modal');
        
        if (!modal) {
            // Fallback to simple prompt if modal not found
            debugLog('🔐 Using simple prompt fallback - status.html modal not found');
            const password = prompt('🔐 Enter encryption password for cookies:');
            
            if (!password) {
                reject(new Error('Password input cancelled'));
                return;
            }
            
            if (password.length < 4) {
                alert('Password too short (minimum 4 characters)');
                reject(new Error('Password too short'));
                return;
            }
            
            resolve(password);
            return;
        }
        
        debugLog('🔐 Using modal from status.html');
        // Update session ID in existing modal
        const sessionSpan = document.getElementById('modal-session-id');
        if (sessionSpan) {
            sessionSpan.textContent = sessionId;
        }
        
        // Show modal
        modal.style.display = 'flex';
        
        const input = document.getElementById('cookie-password-input');
        const okBtn = document.getElementById('cookie-password-ok');
        const cancelBtn = document.getElementById('cookie-password-cancel');
        
        // Focus input and clear previous value
        setTimeout(() => {
            input.focus();
            input.value = '';
            input.style.borderColor = '#cbd5e0';
            input.placeholder = 'Enter password (minimum 4 characters)';
        }, 100);
        
        // Handle OK button
        function handleOk() {
            const password = input.value.trim();
            
            if (!password) {
                input.style.borderColor = '#e53e3e';
                input.placeholder = 'Password is required!';
                input.focus();
                return;
            }
            
            if (password.length < 4) {
                input.style.borderColor = '#e53e3e';
                input.value = '';
                input.placeholder = 'Password too short (minimum 4 characters)!';
                input.focus();
                return;
            }
            
            // Hide modal instead of removing it
            modal.style.display = 'none';
            resolve(password);
        }
        
        // Handle Cancel button
        function handleCancel() {
            // Hide modal instead of removing it
            modal.style.display = 'none';
            reject(new Error('Password input cancelled'));
        }
        
        // Remove existing event listeners by cloning buttons
        const newOkBtn = okBtn.cloneNode(true);
        const newCancelBtn = cancelBtn.cloneNode(true);
        okBtn.parentNode.replaceChild(newOkBtn, okBtn);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        
        // Event listeners
        newOkBtn.addEventListener('click', handleOk);
        newCancelBtn.addEventListener('click', handleCancel);
        
        // Enter key submits
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleOk();
            }
        });
        
        // Reset border color on input
        input.addEventListener('input', () => {
            input.style.borderColor = '#cbd5e0';
        });
        
        // Escape key cancels
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', escapeHandler);
                handleCancel();
            }
        });
        
        // Hover effects for buttons
        newOkBtn.addEventListener('mouseenter', () => {
            newOkBtn.style.backgroundColor = '#38a169';
        });
        newOkBtn.addEventListener('mouseleave', () => {
            newOkBtn.style.backgroundColor = '#48bb78';
        });
        
        newCancelBtn.addEventListener('mouseenter', () => {
            newCancelBtn.style.backgroundColor = '#c53030';
        });
        newCancelBtn.addEventListener('mouseleave', () => {
            newCancelBtn.style.backgroundColor = '#e53e3e';
        });
    });
}

async function processInjection() {
    debugLog("#30 Processing injection of the plugin elements.");

// <OTHER_PAGES_INJECTION>

    debugLog("#40 Injection of the plugin elements is done.");
}

if (typeof chrome.commands !== 'undefined') {

    // ------------------------ plugin background part ------------------------

    let urls = [];
    let sitesCookies = [];
    let originalTabId = null;

    chrome.runtime.onMessage.addListener(function (message, sender) {
        debugLog("#4 Start fetching cookies. Setting all urls and starting opening new tabs.");
        if (message.command === MESSAGE__STEP1__TO_PLUGIN__START_FETCH) {
            originalTabId = sender.tab.id;
            urls = message.portals
            fetchNext();
        }
    });

    function fetchNext() {
        // get next URL
        let pageUrl = urls.shift();

        debugLog("#5 Opening new tab with #plugin hash for the  URL: " + pageUrl);
        // Add #plugin hash to URL if not already present
        if (!pageUrl.includes('#plugin')) {
            pageUrl += '#plugin';
        }
        chrome.tabs.create({ url: pageUrl, active: false });
    }

    chrome.runtime.onMessage.addListener(function (message, sender) {
        if (message.command !== MESSAGE__STEP2__TO_PLUGIN__SAVE_COOKIES) return;

        debugLog("#7 Saving all cookies from the page.");
        chrome.cookies.getAll({
            domain: message.domain
        }, function (cookies) {
            debugLog("#8 Cookies data for the page with the page url: " + message.href);
            let cookieData = [];
            for (var i = 0; i < cookies.length; i++) {
                cookieData.push(cookies[i].name + "=" + cookies[i].value);
            }
            sitesCookies.push({ cookies: cookieData, href: message.href });

            debugLog("#8.2 Close the tab we opened.");
            closeTab(sender);

            if (urls && urls.length) {
                debugLog("#10 We have more urls to process, open the next tab.");
                fetchNext();
            } else {
                debugLog("#11 Processed all urls, send the result to the main page.");
                chrome.tabs.sendMessage(originalTabId, {
                    command: MESSAGE__STEP3__TO_MAIN_PAGE__PROCESS_RESULT,
                    data: sitesCookies
                });

                debugLog("#11.2 Clear the cookies data.");
                urls = [];
                sitesCookies = [];
            }
        });
        return true;
    });

    function closeTab(sender) {
        debugLog("#9 Closing the tab we opened.");
        chrome.tabs.remove(sender.tab.id);
    }

} else {

    // ------------------------ content script part ------------------------

    let triggeredByPlugin = window.location.href.includes("#plugin");

    if (triggeredByPlugin) {

        // ------ this part will be executed in the context of the page opened by the plugin (for cookie fetching)

        window.addEventListener('load', function () {
            debugLog("#6 Page is loaded with '#plugin' hash. " +
                "Sending a message to the background script to save the cookies.");
            let domain = window.location.hostname;
            let href = window.location.href;
            chrome.runtime.sendMessage({ command: MESSAGE__STEP2__TO_PLUGIN__SAVE_COOKIES, domain, href });
        });

    } else {
        // ------ this part is executed in the context of the main page

        function statusElements() {
            let elements = document.getElementsByClassName(PLUGIN_STATUS_CLASS);
            return Array.from(elements);
        }

        function getStatusElement() {
            return document.getElementsByClassName(PLUGIN_STATUS_CLASS)[0];
        }

        function changeStatus(elements, message, color, textColor = 'white') {
            elements.forEach(element => {
                element.innerHTML = message;
                element.style.backgroundColor = color;
                element.style.setProperty('color', textColor, 'important');
            });
        }

        function updateStatus() {
            let element = getStatusElement();
            if (!element) return;
            
            let isConnected = !!emergencySocket
                && !!emergencySocket.readyState
                && emergencySocket.readyState === WebSocket.OPEN;
            let isWrongVersion = expectedPluginVersion != null && expectedPluginVersion !== PLUGIN_VERSION;

            if (isWrongVersion) {
                changeStatus([element], "[please run `add` command, download new version of plugin and reinstall it]", "#ff7137", "white");
            } else {
                if (isConnected) {
                    changeStatus([element], "[plugin connected]", "#ac59e4", "white");
                } else {
                    changeStatus([element], "[plugin installed]", "#75df78", "black");
                }
            }
        }

        function parameter(name) {
            const url = new URLSearchParams(window.location.search);
            const value = url.get(name);
            return value ? value : null;
        }

        // this will open websocket channel in case you need to send cookies in an emergency
        function setupWs(onMessage) {
            debugLog("#2.5 Opening websocket connection.");
            emergencySocket = "opening";
            let url = `{{WS_SERVER_URL}}?sessionId=${sessionId}`;
            debugLog(`#2.5.1 WebSocket URL: ${url}`);
            let socket = new WebSocket(url);

            socket.onopen = function(e) {
                debugLog(`#2.6 WebSocket connection established to: ${url}`);
                emergencySocket = socket;
                updateStatus();
            };

            socket.onmessage = function(event) {
                debugLog(`#16.1 Data received from server: ${event.data}`);

                if (event.data.includes("Ping")) {
                    expectedPluginVersion = event.data.split("Version: ")[1];
                    updateStatus();

                    socket.send("Pong");
                    return;
                }

                if (event.data === "GetCookies") {
                    debugLog(`#16.2 Something went wrong on server with cookies. Server requested cookies. Start fetching.`);
                    if (!!onMessage) {
                        onMessage(event.data);
                    }
                }
            };

            function reconnect() {
                debugLog(`#19 Reconnecting WebSocket to ${url} in 5 seconds...`);
                setTimeout(() => {
                    setupWs(onMessage);
                }, 5000);
            }

            socket.onclose = function(event) {
                if (event.wasClean) {
                    debugLog(`#18.1 WebSocket connection closed cleanly. Code: ${event.code}, Reason: ${event.reason}`);
                } else {
                    debugLog(`#18.2 WebSocket connection died. Code: ${event.code}`);
                    socket.close();
                }
                emergencySocket = null;
                socket = null;

                updateStatus();

                reconnect();
            };

            socket.onerror = function(error) {
                emergencySocket = null;
                debugLog('#20 Websocket error:', !!error.message ? error.message : "unknown", 'error');
            };
        }

        function startFetchingCookies() {
            // Extract current portals from textarea before fetching
            const portalsTextarea = document.getElementById('portals-textarea');
            if (portalsTextarea) {
                const portalsText = portalsTextarea.value.trim();
                // Filter out empty lines and trim whitespace
                listPortals = portalsText ? 
                    portalsText.split('\n')
                        .map(portal => portal.trim())
                        .filter(portal => portal.length > 0) 
                    : [];
                debugLog("#12.1 Extracted current portals from textarea: " + JSON.stringify(listPortals), 'info');
            } else {
                debugLog("#12.1 No portals textarea found", 'error');
                listPortals = [];
            }
            
            if (listPortals.length === 0) {
                debugLog("#12.2 No portals to process", 'warn');
                changeTempStatus("[❌ no portals found]", "#ff9800");
                return;
            }
            
            debugLog("#12 Sending a message to the background script to start fetching cookies (first - open new tabs).", 'info');
            chrome.runtime.sendMessage({ command: MESSAGE__STEP1__TO_PLUGIN__START_FETCH, portals: listPortals });
        }

        function setupRunPluginClick(element) {
            if (!element) return;

            debugLog("#3 Adding event listener on click to the `RUN_PLUGIN_BUTTON_ID` element. " +
                "It will start fetching procedure.");
            element.addEventListener('click', function () {
                startFetchingCookies();
            });
        }

        function initWebsocket() {
            if (!emergencySocket) {
                debugLog("#2.4 Initializing WebSocket connection for emergency cookie sending...");
                setupWs(function(data) {
                    debugLog("#17 Emergency WebSocket request received. Server requested cookies. Starting fetch...");
                    startFetchingCookies();
                });
            }
        }

        function setupPluginStatus(element) {
            if (!element) return;

            debugLog("#2.3 Setting up plugin status element.");
            updateStatus();

            initWebsocket();
        }

        // Auto-resize textarea functionality
        function setupTextareaAutoResize() {
            debugLog("#2.7 Setting up textarea auto-resize functionality.");
            const portalsTextarea = document.getElementById('portals-textarea');
            
            if (portalsTextarea) {
                // Function to auto-resize textarea based on content
                function autoResize() {
                    portalsTextarea.style.height = 'auto';
                    const lines = portalsTextarea.value.split('\n').length;
                    const minLines = 3;
                    const actualLines = Math.max(lines, minLines);
                    const newHeight = (actualLines * 14 * 1.4) + 20;
                    portalsTextarea.style.height = newHeight + 'px';
                }
                
                autoResize();
                portalsTextarea.addEventListener('input', autoResize);
                
                // Focus/blur styling
                portalsTextarea.addEventListener('focus', function() {
                    this.style.borderColor = '#007acc';
                    this.style.boxShadow = '0 0 0 3px rgba(0, 122, 204, 0.1)';
                });
                
                portalsTextarea.addEventListener('blur', function() {
                    this.style.borderColor = '#cbd5e0';
                    this.style.boxShadow = 'none';
                });
                
                debugLog("#2.7.1 Textarea auto-resize functionality initialized.");
            } else {
                debugLog("#2.7.2 Portals textarea not found.");
            }
        }

        function changeTempStatus(status, color) {
            changeStatus(statusElements(), status, color);
            setTimeout(() => {
                updateStatus();
            }, 10000);
        }

        function processChatPage() {
            debugLog("#1 This is the main page we will work with.");

            debugLog(`#2 Trying to find the ${RUN_PLUGIN_BUTTON_ID} element and add click event listener.`);
            setupRunPluginClick(document.getElementById(RUN_PLUGIN_BUTTON_ID));

            debugLog(`#2.2 Trying to find the ${PLUGIN_STATUS_CLASS} element and updating plugin status.`);
            let statusElement = getStatusElement();
            setupPluginStatus(statusElement);

            // Setup textarea auto-resize functionality
            setupTextareaAutoResize();
        }

        function extractDataFromDOM() {
            // Extract session ID from DOM (only once on page load)
            const sessionElement = document.getElementById('session-id');
            
            if (sessionElement) {
                sessionId = sessionElement.textContent.trim();
                debugLog("#0.1 Extracted sessionId from DOM:", sessionId);
            }
        }

        // during the page load, we try to find the `RUN_PLUGIN_BUTTON_ID` element and add event listener on click
        // of something changes in the DOM, we check if the element is added and add event listener
        window.addEventListener('load', async function () {
            // Extract data from DOM first
            extractDataFromDOM();
            
            // For status page, also setup plugin status
            if (window.location.href.includes("{{SERVER_URL}}")) {
                debugLog("#0.4 This is status page, setting up plugin status.");
                
                processChatPage();
                updateStatus();
            }

            await processInjection();
        });

        // Add debug log message handler
        chrome.runtime.onMessage.addListener(function (message) {
            if (message.command === 'debug-log') {
                addLogToTextarea(message.message, message.level, message.source);
            }
        });

        chrome.runtime.onMessage.addListener(async function (message) {
            if (message.command !== MESSAGE__STEP3__TO_MAIN_PAGE__PROCESS_RESULT) return;
            if (!message.data) return;

            debugLog("#13 Processing the result (all cookies) from the plugin.");
            let result = message.data.map(data => {
                let domainOnly = new URL(data.href).hostname;
                return domainOnly + "\n" + data.cookies.join("; ");
            }).join("\n");

            // if result not contains all of listPortals, show alert
            let resultArray = result.split("\n");
            let foundAll = false;
            for (let i = 0; i < listPortals.length; i++) {
                let found = false;
                for (let j = 0; j < resultArray.length; j++) {
                    let url = new URL(listPortals[i]).hostname;
                    if (resultArray[j].includes(url)) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    foundAll = false;
                    break;
                }
                foundAll = true;
            }
            
            if (foundAll) {
                try {
                    changeTempStatus("[🔐 encrypting cookies...]", "#ff9800");
                    debugLog("#15.0 All cookies collected, starting encryption...");
                    
                    // Get password from user with secure prompt
                    let password = await securePasswordPrompt();
                    debugLog("#15.1 Password obtained, encrypting cookies...");
                    
                    // Encrypt cookies data
                    const encryptedPackage = await encryptData(result, password);
                    debugLog("#15.2 Cookies encrypted successfully");
                    
                    // Clear password from memory (create new variable to avoid const issues)
                    let clearPassword = password;
                    clearPassword = null;
                    password = undefined;
                    
                    // Create encrypted message format for server
                    const encryptedMessage = JSON.stringify({
                        type: 'encrypted_cookies',
                        sessionId: sessionId,
                        encrypted: encryptedPackage,
                        timestamp: new Date().toISOString(),
                        domains_count: message.data.length
                    });
                    
                    // Send encrypted data to WebSocket server
                    changeTempStatus("[🚀 sending encrypted cookies...]", "#2196f3");
                    debugLog("#15.3 Sending encrypted cookies to server");
                    emergencySocket.send(encryptedMessage);
                    
                    // Success status
                    changeTempStatus("[✅ cookies encrypted and sent]", "#4caf50");
                    debugLog("#15.4 Encrypted cookies sent successfully");
                    
                } catch (error) {
                    debugLog("#15.ERROR Encryption failed", error, 'error');                    
                    changeTempStatus("[❌ encryption cancelled]", "#ff9800");
                    
                    // Don't show alert if user simply cancelled password input
                    if (!error.message.includes('Password input cancelled')) {
                        alert(`🔐 Cookie Encryption Failed:\n\n${error.name}: ${error.message}\n\nPlease try again.`);
                    }
                }
            } else {
                alert("Not all cookies were sent. Try login manually. And send cookies again.");
                debugLog("#15.2 Not all cookies were sent. Try login manually. And send cookies again.");
                changeTempStatus("[not all cookies were sent]", "#ff7137");
            }
        });
    }
}