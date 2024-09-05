var E, O, k = {
        exports: {}
    }, j = {
        exports: {}
    };
    E = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    O = {
        rotl: function(t, e) {
            return t << e | t >>> 32 - e
        },
        rotr: function(t, e) {
            return t << 32 - e | t >>> e
        },
        endian: function(t) {
            if (t.constructor == Number)
                return 16711935 & O.rotl(t, 8) | 4278255360 & O.rotl(t, 24);
            for (var e = 0; e < t.length; e++)
                t[e] = O.endian(t[e]);
            return t
        },
        randomBytes: function(t) {
            for (var e = []; t > 0; t--)
                e.push(Math.floor(256 * Math.random()));
            return e
        },
        bytesToWords: function(t) {
            for (var e = [], n = 0, r = 0; n < t.length; n++,
            r += 8)
                e[r >>> 5] |= t[n] << 24 - r % 32;
            return e
        },
        wordsToBytes: function(t) {
            for (var e = [], n = 0; n < 32 * t.length; n += 8)
                e.push(t[n >>> 5] >>> 24 - n % 32 & 255);
            return e
        },
        bytesToHex: function(t) {
            for (var e = [], n = 0; n < t.length; n++)
                e.push((t[n] >>> 4).toString(16)),
                e.push((15 & t[n]).toString(16));
            return e.join("")
        },
        hexToBytes: function(t) {
            for (var e = [], n = 0; n < t.length; n += 2)
                e.push(parseInt(t.substr(n, 2), 16));
            return e
        },
        bytesToBase64: function(t) {
            for (var e = [], n = 0; n < t.length; n += 3)
                for (var r = t[n] << 16 | t[n + 1] << 8 | t[n + 2], o = 0; o < 4; o++)
                    8 * n + 6 * o <= 8 * t.length ? e.push(E.charAt(r >>> 6 * (3 - o) & 63)) : e.push("=");
            return e.join("")
        },
        base64ToBytes: function(t) {
            t = t.replace(/[^A-Z0-9+\/]/gi, "");
            for (var e = [], n = 0, r = 0; n < t.length; r = ++n % 4)
                0 != r && e.push((E.indexOf(t.charAt(n - 1)) & Math.pow(2, -2 * r + 8) - 1) << 2 * r | E.indexOf(t.charAt(n)) >>> 6 - 2 * r);
            return e
        }
    },
    j.exports = O;
    var C = j.exports
      , T = {
        utf8: {
            stringToBytes: function(t) {
                return T.bin.stringToBytes(unescape(encodeURIComponent(t)))
            },
            bytesToString: function(t) {
                return decodeURIComponent(escape(T.bin.bytesToString(t)))
            }
        },
        bin: {
            stringToBytes: function(t) {
                for (var e = [], n = 0; n < t.length; n++)
                    e.push(255 & t.charCodeAt(n));
                return e
            },
            bytesToString: function(t) {
                for (var e = [], n = 0; n < t.length; n++)
                    e.push(String.fromCharCode(t[n]));
                return e.join("")
            }
        }
    }
      , _ = T
      , R = function(t) {
        return null != t && (P(t) || function(t) {
            return "function" == typeof t.readFloatLE && "function" == typeof t.slice && P(t.slice(0, 0))
        }(t) || !!t._isBuffer)
    };
    function P(t) {
        return !!t.constructor && "function" == typeof t.constructor.isBuffer && t.constructor.isBuffer(t)
    }
    function main(arg1) {
        var t = C
          , e = _.utf8
          , n = R
          , r = _.bin
          , o = function o(i, a) {
            i.constructor == String ? i = a && "binary" === a.encoding ? r.stringToBytes(i) : e.stringToBytes(i) : n(i) ? i = Array.prototype.slice.call(i, 0) : Array.isArray(i) || i.constructor === Uint8Array || (i = i.toString());
            for (var c = t.bytesToWords(i), u = 8 * i.length, s = 1732584193, l = -271733879, f = -1732584194, p = 271733878, d = 0; d < c.length; d++)
                c[d] = 16711935 & (c[d] << 8 | c[d] >>> 24) | 4278255360 & (c[d] << 24 | c[d] >>> 8);
            c[u >>> 5] |= 128 << u % 32,
            c[14 + (u + 64 >>> 9 << 4)] = u;
            var h = o._ff
              , v = o._gg
              , y = o._hh
              , m = o._ii;
            for (d = 0; d < c.length; d += 16) {
                var g = s
                  , b = l
                  , w = f
                  , A = p;
                s = h(s, l, f, p, c[d + 0], 7, -680876936),
                p = h(p, s, l, f, c[d + 1], 12, -389564586),
                f = h(f, p, s, l, c[d + 2], 17, 606105819),
                l = h(l, f, p, s, c[d + 3], 22, -1044525330),
                s = h(s, l, f, p, c[d + 4], 7, -176418897),
                p = h(p, s, l, f, c[d + 5], 12, 1200080426),
                f = h(f, p, s, l, c[d + 6], 17, -1473231341),
                l = h(l, f, p, s, c[d + 7], 22, -45705983),
                s = h(s, l, f, p, c[d + 8], 7, 1770035416),
                p = h(p, s, l, f, c[d + 9], 12, -1958414417),
                f = h(f, p, s, l, c[d + 10], 17, -42063),
                l = h(l, f, p, s, c[d + 11], 22, -1990404162),
                s = h(s, l, f, p, c[d + 12], 7, 1804603682),
                p = h(p, s, l, f, c[d + 13], 12, -40341101),
                f = h(f, p, s, l, c[d + 14], 17, -1502002290),
                s = v(s, l = h(l, f, p, s, c[d + 15], 22, 1236535329), f, p, c[d + 1], 5, -165796510),
                p = v(p, s, l, f, c[d + 6], 9, -1069501632),
                f = v(f, p, s, l, c[d + 11], 14, 643717713),
                l = v(l, f, p, s, c[d + 0], 20, -373897302),
                s = v(s, l, f, p, c[d + 5], 5, -701558691),
                p = v(p, s, l, f, c[d + 10], 9, 38016083),
                f = v(f, p, s, l, c[d + 15], 14, -660478335),
                l = v(l, f, p, s, c[d + 4], 20, -405537848),
                s = v(s, l, f, p, c[d + 9], 5, 568446438),
                p = v(p, s, l, f, c[d + 14], 9, -1019803690),
                f = v(f, p, s, l, c[d + 3], 14, -187363961),
                l = v(l, f, p, s, c[d + 8], 20, 1163531501),
                s = v(s, l, f, p, c[d + 13], 5, -1444681467),
                p = v(p, s, l, f, c[d + 2], 9, -51403784),
                f = v(f, p, s, l, c[d + 7], 14, 1735328473),
                s = y(s, l = v(l, f, p, s, c[d + 12], 20, -1926607734), f, p, c[d + 5], 4, -378558),
                p = y(p, s, l, f, c[d + 8], 11, -2022574463),
                f = y(f, p, s, l, c[d + 11], 16, 1839030562),
                l = y(l, f, p, s, c[d + 14], 23, -35309556),
                s = y(s, l, f, p, c[d + 1], 4, -1530992060),
                p = y(p, s, l, f, c[d + 4], 11, 1272893353),
                f = y(f, p, s, l, c[d + 7], 16, -155497632),
                l = y(l, f, p, s, c[d + 10], 23, -1094730640),
                s = y(s, l, f, p, c[d + 13], 4, 681279174),
                p = y(p, s, l, f, c[d + 0], 11, -358537222),
                f = y(f, p, s, l, c[d + 3], 16, -722521979),
                l = y(l, f, p, s, c[d + 6], 23, 76029189),
                s = y(s, l, f, p, c[d + 9], 4, -640364487),
                p = y(p, s, l, f, c[d + 12], 11, -421815835),
                f = y(f, p, s, l, c[d + 15], 16, 530742520),
                s = m(s, l = y(l, f, p, s, c[d + 2], 23, -995338651), f, p, c[d + 0], 6, -198630844),
                p = m(p, s, l, f, c[d + 7], 10, 1126891415),
                f = m(f, p, s, l, c[d + 14], 15, -1416354905),
                l = m(l, f, p, s, c[d + 5], 21, -57434055),
                s = m(s, l, f, p, c[d + 12], 6, 1700485571),
                p = m(p, s, l, f, c[d + 3], 10, -1894986606),
                f = m(f, p, s, l, c[d + 10], 15, -1051523),
                l = m(l, f, p, s, c[d + 1], 21, -2054922799),
                s = m(s, l, f, p, c[d + 8], 6, 1873313359),
                p = m(p, s, l, f, c[d + 15], 10, -30611744),
                f = m(f, p, s, l, c[d + 6], 15, -1560198380),
                l = m(l, f, p, s, c[d + 13], 21, 1309151649),
                s = m(s, l, f, p, c[d + 4], 6, -145523070),
                p = m(p, s, l, f, c[d + 11], 10, -1120210379),
                f = m(f, p, s, l, c[d + 2], 15, 718787259),
                l = m(l, f, p, s, c[d + 9], 21, -343485551),
                s = s + g >>> 0,
                l = l + b >>> 0,
                f = f + w >>> 0,
                p = p + A >>> 0
            }
            return t.endian([s, l, f, p])
        };
        o._ff = function(t, e, n, r, o, i, a) {
            var c = t + (e & n | ~e & r) + (o >>> 0) + a;
            return (c << i | c >>> 32 - i) + e
        }
        ,
        o._gg = function(t, e, n, r, o, i, a) {
            var c = t + (e & r | n & ~r) + (o >>> 0) + a;
            return (c << i | c >>> 32 - i) + e
        }
        ,
        o._hh = function(t, e, n, r, o, i, a) {
            var c = t + (e ^ n ^ r) + (o >>> 0) + a;
            return (c << i | c >>> 32 - i) + e
        }
        ,
        o._ii = function(t, e, n, r, o, i, a) {
            var c = t + (n ^ (e | ~r)) + (o >>> 0) + a;
            return (c << i | c >>> 32 - i) + e
        }
        ,
        o._blocksize = 16,
        o._digestsize = 16,
        result = function() {
            var n = undefined
            if (null == arg1)
                throw new Error("Illegal argument " + e);
                var i = t.wordsToBytes(o(arg1, n));
            return n && n.asBytes ? i : n && n.asString ? r.bytesToString(i) : t.bytesToHex(i)
        }
        return result()
    };
function mainf(argv) {
    const wts = Math.round(Date.now() / 1e3);
    return {'wts':wts,'sign':main(`mid=${argv}&platform=web&token=&web_location=1550101&wts=${wts}`+"ea1db124af3c7062474693fa704f4ff8")}
}

console.log(mainf('348933131'))
