importScripts('/home/hatzimin/we/indivo_ui_server/apps/procedures/static/js/speakGenerator.js');

onmessage = function(event) {
  postMessage(generateSpeech(event.data.text, event.data.args));
};

