var isFlashEnabled;
var getFlashVersion;
var isUsingPepperFlash;
var isUsingActiveX;

//
// SOURCES FOR MUCH OF THIS CODE:
//   - https://code.google.com/p/doctype-mirror/wiki/ArticleDetectFlash#The_code
//   - http://stackoverflow.com/questions/12866060/detecting-pepper-ppapi-flash-with-javascript
//
(function () {
    var hasFlash = false;
    var isActiveX = false;
    var flashVersion = '';
    var isPPAPI = false;

    /**
     * Derived from Apple's suggested sniffer.
     * @param {String} desc e.g. "Shockwave Flash 7.0 r61"
     * @return {String} "7.0.61"
     * @private
     */
    function parseFlashVersion(desc) {
        var matches = desc.match(/[\d]+/g);
        matches.length = 3; // To standardize IE vs FF
        return matches.join('.');
    }

    function isPepperFlash(flashPlayerFileName) {
        return !!flashPlayerFileName && (flashPlayerFileName = flashPlayerFileName.toLowerCase()) && (
        flashPlayerFileName === "pepflashplayer.dll" || flashPlayerFileName === "libpepflashplayer.so" || flashPlayerFileName === "pepperflashplayer.plugin" || flashPlayerFileName.slice(-13) === "chrome.plugin");
    }

    function inspectPlugin(plugin) {
        if (plugin) {
            hasFlash = true;
            if (plugin.version) {
                flashVersion = parseFlashVersion(plugin.version);
            }
            if (!flashVersion && plugin.description) {
                flashVersion = parseFlashVersion(plugin.description);
            }
            if (plugin.filename) {
                isPPAPI = isPepperFlash(plugin.filename);
            }
        }
    }

    var plugin, ax, mimeType;

    if (navigator.plugins && navigator.plugins.length) {
        plugin = navigator.plugins['Shockwave Flash'];
        inspectPlugin(plugin);

        if (navigator.plugins['Shockwave Flash 2.0']) {
            hasFlash = true;
            flashVersion = '2.0.0.11';
        }
    } else if (navigator.mimeTypes && navigator.mimeTypes.length) {
        mimeType = navigator.mimeTypes['application/x-shockwave-flash'];
        plugin = mimeType && mimeType.enabledPlugin;
        inspectPlugin(plugin);
    } else if (typeof ActiveXObject !== 'undefined') {
        //
        // Using IE < 11
        //
        
        isActiveX = true;

        try {
            // Try 7 first, since we know we can use GetVariable with it
            ax = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.7');
            hasFlash = true;
            flashVersion = parseFlashVersion(ax.GetVariable('$version'));
        } catch (e) {
            // Try 6 next, some versions are known to crash with GetVariable calls
            try {
                ax = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.6');
                hasFlash = true;
                flashVersion = '6.0.21'; // First public version of Flash 6
            } catch (e) {
                try {
                    // Try the default ActiveX
                    ax = new ActiveXObject('ShockwaveFlash.ShockwaveFlash');
                    hasFlash = true;
                    flashVersion = parseFlashVersion(ax.GetVariable('$version'));
                } catch (e) {
                    // No flash
                    isActiveX = false;
                }
            }
        }
    }

    /**
     * Is Flash enabled?
     * @type Boolean
     */
    isFlashEnabled = function () {
        return hasFlash;
    };


    /**
     * Full version information of flash installed, in the format "7.0.61"
     * @type String
     */
    getFlashVersion = function () {
        return flashVersion || '0.0.0';
    };

    /**
     * @type Boolean
     */
    isUsingPepperFlash = function () {
        return isPPAPI;
    };
    
    /**
     * @type Boolean
     */
    isUsingActiveX = function () {
        return isActiveX;
    };    

})();

