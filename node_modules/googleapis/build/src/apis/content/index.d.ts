import { content_v2 } from './v2';
export declare const VERSIONS: {
    'v2': typeof content_v2.Content;
};
export declare function content(version: 'v2'): content_v2.Content;
export declare function content(options: content_v2.Options): content_v2.Content;
