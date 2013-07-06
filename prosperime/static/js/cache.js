/* Super Simple client-side cache that hides details so we 
		can muddle with them later */
	function ClientCache() {
		this.cache = {}
	};

	ClientCache.prototype.get = function(key) {
		return this.cache[key]
	};

	ClientCache.prototype.keys = function() {
		return Object.keys(this.cache)
	};

	ClientCache.prototype.set = function(key, value) {
		this.cache[key] = value
		return true;
	};

	ClientCache.prototype.contains = function(key) {
		return key in this.cache
	};

	// string -> hash fxn from SO
	ClientCache.prototype.generateKey = function(string) {
		var hash = 0, i, char;
	    if (string.length == 0) return hash;
	    for (i = 0, l = string.length; i < l; i++) {
	        char  = string.charCodeAt(i);
	        hash  = ((hash<<5)-hash)+char;
	        hash |= 0; // Convert to 32bit integer
	    }
	    return hash;
	};

	ClientCache.prototype.clear = function() {
		this.cache = {}
	};
	