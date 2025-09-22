/**
 * Indian Number System Formatting Utilities
 */

// Format number to Indian currency system
function formatIndianNumber(num) {
    // Handle negative numbers
    const isNegative = num < 0;
    num = Math.abs(num);
    
    if (num >= 10000000) { // Crores
        const crores = (num / 10000000).toFixed(2);
        return (isNegative ? '-' : '') + '₹' + crores + ' Cr';
    } else if (num >= 100000) { // Lakhs
        const lakhs = (num / 100000).toFixed(2);
        return (isNegative ? '-' : '') + '₹' + lakhs + ' L';
    } else if (num >= 1000) { // Thousands
        const thousands = (num / 1000).toFixed(1);
        return (isNegative ? '-' : '') + '₹' + thousands + 'K';
    } else {
        return (isNegative ? '-' : '') + '₹' + num.toFixed(0);
    }
}

// Format with commas (Indian style: 12,34,567)
function addIndianCommas(num) {
    num = num.toString();
    let lastThree = num.substring(num.length - 3);
    let otherNumbers = num.substring(0, num.length - 3);
    if (otherNumbers != '') {
        lastThree = ',' + lastThree;
    }
    return otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + lastThree;
}

// Export functions
window.formatIndianNumber = formatIndianNumber;
window.addIndianCommas = addIndianCommas;