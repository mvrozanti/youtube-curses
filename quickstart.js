#!/usr/bin/env node
var path = require('path')
var fs = require('fs');
var readline = require('readline');
var {google} = require('googleapis');
var OAuth2 = google.auth.OAuth2;

var SCOPES = ['https://www.googleapis.com/auth/youtube.readonly'];
var TOKEN_DIR = (process.env.HOME || process.env.HOMEPATH || process.env.USERPROFILE) + '/.credentials/';
var TOKEN_PATH = path.resolve(__dirname, 'credentials.dat')

function main(){
    var ArgumentParser = require('argparse').ArgumentParser;
    var parser = new ArgumentParser({
      version: '1.0.0',
      addHelp:true,
      description: 'This is a simple youtube browser / streamlink frontend made with python and ncurses inspired by twitch-curses'
    });
    parser.addArgument([ '-f', '--foo' ], { help: 'foo bar' });
    parser.addArgument([ '-b', '--bar' ], { help: 'bar foo' });
    parser.addArgument('--baz', { help: 'baz bar' });
    var args = parser.parseArgs();
    fs.readFile('client_secret.json', function processClientSecrets(err, content) {
        if (err) { console.log('Error loading client secret file: ' + err); return; }
        authorize(JSON.parse(content), getNewestSubscriptions);
    });
}

function authorize(credentials, callback) {
    var clientSecret = credentials.installed.client_secret;
    var clientId = credentials.installed.client_id;
    var redirectUrl = credentials.installed.redirect_uris[0];
    var oauth2Client = new OAuth2(clientId, clientSecret, redirectUrl);

    fs.readFile(TOKEN_PATH, function(err, token) {
        if (err) {
            getNewToken(oauth2Client, callback);
        } else {
            oauth2Client.credentials = JSON.parse(token);
            callback(oauth2Client);
        }
    });
}

function getNewToken(oauth2Client, callback) {
    var authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES
    });
    console.log('Authorize this app by visiting this url: ', authUrl);
    var rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    rl.question('Enter the code from that page here: ', function(code) {
        rl.close();
        oauth2Client.getToken(code, function(err, token) {
            if (err) { console.log('Error while trying to retrieve access token', err); return; }
            oauth2Client.credentials = token;
            storeToken(token);
            callback(oauth2Client);
        });
    });
}

function storeToken(token) {
    try { fs.mkdirSync(TOKEN_DIR); } catch (err) { if (err.code != 'EEXIST') { throw err; } }
    fs.writeFile(TOKEN_PATH, JSON.stringify(token), (err) => {
        if (err) throw err;
        console.log('Token stored to ' + TOKEN_PATH);
    });
    console.log('Token stored to ' + TOKEN_PATH);
}

function getNewestSubscriptions(auth) {
var service = google.youtube('v3');
  var parameters = {'auth':auth, 'maxResults': 5, home: true, 'part': 'snippet,contentDetails'};
  return service.subscriptions.list(parameters, function(err, response) {
    if (err) { console.log('The API returned an error: ' + err); return; }
    for(i of response.data.items){
        service.search.list({
            auth: auth,
            part: 'snippet',
            channelId: i.snippet.channelId,
        }, function(err, response) {
            if (err) { console.log('The API returned an error: ' + err); return; }
            console.log(response.data.items)
        });
    }
  });
}

function subscriptionsListMySubscriptions(auth, requestData) {
  var service = google.youtube('v3');
  var parameters = {'auth':auth, 'maxResults': 50, 'mine': 'true', 'part': 'snippet,contentDetails'};
  return service.subscriptions.list(parameters, function(err, response) {
    if (err) { console.log('The API returned an error: ' + err); return; }
    console.log(response.data.items);
  });
}

function getChannel(auth, channel) {
    var service = google.youtube('v3');
    service.channels.list({
        auth: auth,
        part: 'snippet,contentDetails,statistics',
        forUsername: channel || 'GoogleDevelopers'
    }, function(err, response) {
        if (err) { console.log('The API returned an error: ' + err); return; }
        var channels = response.data.items;
        console.log(channels)
    });
}

main()
