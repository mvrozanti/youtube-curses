import { videointelligence_v1 } from './v1';
import { videointelligence_v1beta2 } from './v1beta2';
import { videointelligence_v1p1beta1 } from './v1p1beta1';
export declare const VERSIONS: {
    'v1': typeof videointelligence_v1.Videointelligence;
    'v1beta2': typeof videointelligence_v1beta2.Videointelligence;
    'v1p1beta1': typeof videointelligence_v1p1beta1.Videointelligence;
};
export declare function videointelligence(version: 'v1'): videointelligence_v1.Videointelligence;
export declare function videointelligence(options: videointelligence_v1.Options): videointelligence_v1.Videointelligence;
export declare function videointelligence(version: 'v1beta2'): videointelligence_v1beta2.Videointelligence;
export declare function videointelligence(options: videointelligence_v1beta2.Options): videointelligence_v1beta2.Videointelligence;
export declare function videointelligence(version: 'v1p1beta1'): videointelligence_v1p1beta1.Videointelligence;
export declare function videointelligence(options: videointelligence_v1p1beta1.Options): videointelligence_v1p1beta1.Videointelligence;
