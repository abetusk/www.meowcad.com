(function() {
    'use strict';
    
    var fs          = require('fs'),
        tryCatch    = require('try-catch');
    
    module.exports = function(name, callback) {
        check(name);
        checkCB(callback);
        
        fs.readFile(name, 'utf8', function(error, data) {
            var json;
            
            if (!error)
                error = tryCatch(function() {
                    json = JSON.parse(data);
                });
            
            callback(error, json);
        });
    };
    
    module.exports.sync = sync;
    
    function sync(name) {
        check(name);
        
        var data = fs.readFileSync(name, 'utf8'),
            json = JSON.parse(data);
            
        return json;
    }
    
    module.exports.sync.try = function(name) {
        check(name);
        
        var data;
        
        tryCatch(function() {
            data = sync(name);
        });
        
        return data;
    };
    
    function check(name) {
        if (typeof name !== 'string')
            throw Error('name should be string!');
    }
    
    function checkCB(callback) {
        if (typeof callback !== 'function')
            throw Error('callback should be function!');
    }
})();
