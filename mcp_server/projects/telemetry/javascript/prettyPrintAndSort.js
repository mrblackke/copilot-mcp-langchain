/**
 * Pretty prints and sorts telemetry data using the provided order map.
 * 
 * @param {Object} params - Parameters object
 * @param {Array} params.data - The telemetry data array
 * @param {Object} params.orderMap - The order map for field sorting
 * @returns {Array} Sorted and pretty formatted data
 */
function prettyPrintAndSort(params) {
    const data = params.data;
    const orderMap = params.orderMap;
    
    if (!Array.isArray(data)) {
        return data;
    }
    
    function sortObjectKeys(obj, currentPath = '') {
        if (Array.isArray(obj)) {
            return obj.map(item => sortObjectKeys(item, currentPath))
                .sort((a, b) => {
                    // Sort objects with name field alphabetically by name
                    if (a && typeof a === "object" && b && typeof b === "object" && 'name' in a && 'name' in b) {
                        return a.name.localeCompare(b.name, undefined, { numeric: true });
                    }
                    // Sort numbers numerically
                    if (typeof a === "number" && typeof b === "number") {
                        return a - b;
                    }
                    // Default string comparison
                    return String(a).localeCompare(String(b), undefined, { numeric: true });
                });
        } else if (obj !== null && typeof obj === 'object') {
            const sortedObj = {};
            const keyOrder = orderMap[currentPath] || [];
            
            // Get keys that are in the order map and exist in the object
            const orderedKeys = keyOrder.filter(key => key in obj);
            // Get remaining keys not in the order map, sorted alphabetically
            const unorderedKeys = Object.keys(obj).filter(key => !keyOrder.includes(key)).sort();
            
            // Combine ordered keys first, then unordered keys
            const allKeys = [...orderedKeys, ...unorderedKeys];
            
            for (const key of allKeys) {
                const newPath = currentPath ? `${currentPath}.${key}` : key;
                sortedObj[key] = sortObjectKeys(obj[key], newPath);
            }
            return sortedObj;
        }
        return obj;
    }
    
    try {
        const sortedData = data.map(item => sortObjectKeys(item));
        return sortedData;
    } catch (e) {
        return data; // Return original data if sorting fails
    }
}