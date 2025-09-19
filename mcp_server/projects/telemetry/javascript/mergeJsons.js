function mergeJsons(parameters) {
    let { json_arrays } = parameters;
    // If json_arrays is a string, try to parse it as JSON first
    if (typeof json_arrays === 'string') {
        try {
            json_arrays = JSON.parse(json_arrays);
        } catch (e) {
            return [];
        }
    }
    if (!Array.isArray(json_arrays)) {
        return [];
    }
    // Parse each array if it's a string, or use directly if it's already an array
    const parsedArrays = json_arrays.map(arr => {
        if (typeof arr === 'string') {
            try {
                return JSON.parse(arr);
            } catch (e) {
                return [];
            }
        }
        if (Array.isArray(arr)) {
            return arr;
        }
        if (typeof arr === 'object' && arr !== null) {
            return [arr];
        }
        return [];
    });
    // Merge all arrays into one
    let mergedJson = parsedArrays.flat();
    // Глубокая рекурсивная распаковка всех строк-массивов и строк-объектов на любом уровне вложенности
    function deepParseAny(value) {
        if (typeof value === 'string') {
            try {
                const parsed = JSON.parse(value);
                return deepParseAny(parsed);
            } catch (e) {
                return value;
            }
        } else if (Array.isArray(value)) {
            // flatMap для рекурсивной распаковки вложенных массивов
            return value.flatMap(item => deepParseAny(item));
        } else if (value && typeof value === 'object') {
            for (const key in value) {
                if (Object.prototype.hasOwnProperty.call(value, key)) {
                    value[key] = deepParseAny(value[key]);
                }
            }
            return value;
        }
        return value;
    }
    mergedJson = deepParseAny(mergedJson);

    // Финальная распаковка: если в массиве остались строки-массивы, разворачиваем их на верхнем уровне
    function flattenStringifiedArrays(arr) {
        let changed = false;
        let result = arr.flatMap(item => {
            if (typeof item === 'string') {
                try {
                    const parsed = JSON.parse(item);
                    if (Array.isArray(parsed)) {
                        changed = true;
                        return parsed;
                    }
                    return [parsed];
                } catch (e) {
                    return [item];
                }
            }
            return [item];
        });
        if (changed) {
            return flattenStringifiedArrays(result);
        }
        return result;
    }
    if (Array.isArray(mergedJson)) {
        mergedJson = flattenStringifiedArrays(mergedJson);
        // Финальная фильтрация: если остались строки-массивы, полностью заменяем их на содержимое
        let changed = true;
        while (changed) {
            changed = false;
            mergedJson = mergedJson.flatMap(item => {
                if (typeof item === 'string') {
                    try {
                        const parsed = JSON.parse(item);
                        if (Array.isArray(parsed)) {
                            changed = true;
                            return parsed;
                        }
                        return [parsed];
                    } catch (e) {
                        return [item];
                    }
                }
                return [item];
            });
        }
        // Оставляем только объекты
        mergedJson = mergedJson.filter(item => typeof item === 'object' && item !== null && !Array.isArray(item));
    }
    // Remove duplicates by date (keep the last occurrence)
    const uniqueJson = [];
    const dates = new Set();
    for (let i = mergedJson.length - 1; i >= 0; i--) {
        if (mergedJson[i] && typeof mergedJson[i] === 'object' && !dates.has(mergedJson[i].date)) {
            dates.add(mergedJson[i].date);
            uniqueJson.unshift(mergedJson[i]);
        }
    }
    // Sort by date
    uniqueJson.sort((a, b) => new Date(a.date) - new Date(b.date));

    // FINAL GUARD: If uniqueJson is a single stringified array, parse and flatten it
    if (uniqueJson.length === 1 && typeof uniqueJson[0] === 'string') {
        try {
            const parsed = JSON.parse(uniqueJson[0]);
            if (Array.isArray(parsed)) {
                // Only keep objects
                return parsed.filter(item => typeof item === 'object' && item !== null && !Array.isArray(item));
            }
        } catch (e) {
            // fall through
        }
    }
    return uniqueJson;
}