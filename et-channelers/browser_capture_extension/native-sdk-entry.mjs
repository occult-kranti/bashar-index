import {SabrStream} from 'googlevideo/sabr-stream';
import {EnabledTrackTypes,Logger,buildSabrFormat} from 'googlevideo/utils';
import {VideoPlaybackAbrRequest,FormatXTags} from 'googlevideo/protos';
import {openNativeSabr,NativeSabrError} from 'native-sabr-project-adapter';

// Permanently silence this private bundled SDK instance. Upstream diagnostics
// can contain signed transport URLs, so consumers cannot re-enable its logger.
Logger.getInstance().setLogLevels(0);
Logger.prototype.log=()=>{};
Logger.prototype.setLogLevels=function(){this.currentLogLevels=new Set();};
const sdk=Object.freeze({SabrStream,EnabledTrackTypes,Logger,FormatXTags,VideoPlaybackAbrRequest,version:'5.0.1'});
const api=Object.freeze({schemaVersion:1,sdkVersion:'5.0.1',sdk,SabrStream,
  EnabledTrackTypes,Logger,buildSabrFormat,VideoPlaybackAbrRequest,FormatXTags,
  openNativeSabr,NativeSabrError});
if(Object.prototype.hasOwnProperty.call(globalThis,'ChannelingNativeSabrV1')){
  throw new Error('native_sdk_namespace_already_installed');
}
Object.defineProperty(globalThis,'ChannelingNativeSabrV1',{value:api,writable:false,configurable:false});
