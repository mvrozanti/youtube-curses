"use strict";
/**
 * Copyright 2012 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const axios_1 = require("axios");
const options_1 = require("./options");
// tslint:disable-next-line variable-name
const HttpsProxyAgent = require('https-proxy-agent');
// tslint:disable-next-line no-var-requires
const pkg = require('../../package.json');
const PRODUCT_NAME = 'google-api-nodejs-client';
/**
 * Axios will use XHR if it is available. In the case of Electron,
 * since XHR is there it will try to use that. This leads to OPTIONS
 * preflight requests which googleapis DOES NOT like. This line of
 * code pins the adapter to ensure it uses node.
 * https://github.com/google/google-api-nodejs-client/issues/1083
 */
axios_1.default.defaults.adapter = require('axios/lib/adapters/http');
class DefaultTransporter {
    /**
     * Configures request options before making a request.
     * @param opts AxiosRequestConfig options.
     * @return Configured options.
     */
    configure(opts = {}) {
        // set transporter user agent
        opts.headers = opts.headers || {};
        const uaValue = opts.headers['User-Agent'];
        if (!uaValue) {
            opts.headers['User-Agent'] = DefaultTransporter.USER_AGENT;
        }
        else if (!uaValue.includes(`${PRODUCT_NAME}/`)) {
            opts.headers['User-Agent'] =
                `${uaValue} ${DefaultTransporter.USER_AGENT}`;
        }
        return opts;
    }
    request(opts, callback) {
        // ensure the user isn't passing in request-style options
        opts = this.configure(opts);
        try {
            options_1.validate(opts);
        }
        catch (e) {
            if (callback) {
                return callback(e);
            }
            else {
                throw e;
            }
        }
        // If the user configured an `HTTPS_PROXY` environment variable, create
        // a custom agent to proxy the request.
        const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
        if (proxy) {
            opts.httpsAgent = new HttpsProxyAgent(proxy);
            opts.proxy = false;
        }
        if (callback) {
            axios_1.default(opts).then(r => {
                callback(null, r);
            }, e => {
                callback(this.processError(e));
            });
        }
        else {
            return axios_1.default(opts).catch(e => {
                throw this.processError(e);
            });
        }
    }
    /**
     * Changes the error to include details from the body.
     */
    processError(e) {
        const res = e.response;
        const err = e;
        const body = res ? res.data : null;
        if (res && body && body.error && res.status !== 200) {
            if (typeof body.error === 'string') {
                err.message = body.error;
                err.code = res.status.toString();
            }
            else if (Array.isArray(body.error.errors)) {
                err.message =
                    body.error.errors.map((err2) => err2.message).join('\n');
                err.code = body.error.code;
                err.errors = body.error.errors;
            }
            else {
                err.message = body.error.message;
                err.code = body.error.code || res.status;
            }
        }
        else if (res && res.status >= 400) {
            // Consider all 4xx and 5xx responses errors.
            err.message = body;
            err.code = res.status.toString();
        }
        return err;
    }
}
/**
 * Default user agent.
 */
DefaultTransporter.USER_AGENT = `${PRODUCT_NAME}/${pkg.version}`;
exports.DefaultTransporter = DefaultTransporter;
//# sourceMappingURL=transporters.js.map