import { Component, ViewChild, ElementRef, Input } from '@angular/core';
import { NavController, ToastController } from 'ionic-angular';
import { Diagnostic } from '@ionic-native/diagnostic'
import { shaka } from '../../js-libs/shaka-player';
//npm install shaka-player --save
import { Network } from '@ionic-native/network';

@Component({
  selector: 'page-home',
  templateUrl: 'home.html'
})
export class HomePage {

  private manifestUri = ''
  private kid = ''
  private value = ''

  // @Input('vidName') vidName:string
  /*
  This can be converted to a component which has vidName as an attribute, 

  1.videos will be loaded from s3 bucket with
  this.manifestUri = 'https://s3.ap-south-1.amazonaws.com/.../'+vidName+'/dash/manifest.mpd'
  accordingly keys can be loaded from the same link with the vidName
  
  2.videos will be loaded from sd card with
  sdpath+='/video_offline/'+vidName+'/dash/manifest.mpd'
  and keys can be loaded from the app root directory using File plugin
  
  First getOfflineData is executed and it calls getOnlineData if any of the following conditions are met
  1. No SD Card
  2. No File in SD Card
  
  -playVideo() plays the video, pauseVideo() pauses the video
  
  -there is a  timeout of 1 second after ngAfterViewInit() to let the CDV server start for webview,
   there may be a better method for this idk.
  -there is a timeout of 100 milli seconds after URL is converted for server to let it give a URL before
   the player is initallised. There may be a better method for this too idk.
  
  -Webview version 3.0.0 does not work with this code, Webview must be installed as a plugin and npm
   library, this uses version 2.1.3 and it works. Don't need to declare webview as a provider in module.ts
   
  -config.xml should have these lines
    <access origin="http://localhost:8080" />
    <allow-navigation href="http://localhost:8080/*" />
    <allow-intent href="http://localhost:8080/*" />
  
  -there is nothing if user denies use of sd card but I'm sure it can be added easily
  
  Important links for help?
  -http://shaka-player-demo.appspot.com
  -https://stackoverflow.com/questions/34692092/cordova-check-if-file-in-url-exists
  -https://github.com/dpa99c/cordova-diagnostic-plugin#getexternalsdcarddetails

   */

  constructor(
    public navCtrl: NavController,
    private diagnostic: Diagnostic,
    private toast: ToastController, 
    private network: Network
  ) {

  }

  private win: any = window;
  @ViewChild('drmVideo') private drmVideo: ElementRef;

  public getOfflinePath() {
    this.diagnostic.requestExternalStorageAuthorization().then( (state) => {
      let sdpath:string
      console.log(state)
      this.diagnostic.getExternalSdCardDetails()
			.then( (data) => {
        if(data.length==0){ //checks if sd card exists

          this.getOnlineData()
        
        } else {
        
          sdpath = data[0].filePath;
          sdpath += '/tohost/dash/manifest.mpd';
          this.win.resolveLocalFileSystemURL(sdpath,()=>{ //if file does exist
            var convUrl = this.win.Ionic.WebView.convertFileSrc(sdpath);
            this.manifestUri = convUrl;
            setTimeout(()=>{
              this.initPlayer()
            },100) //vvshady
          },()=>{ //if file does not exist
            this.getOnlineData();
          });
        
        }
			}, (errData)=>{
				console.error(errData);
      });	
    }
    )
  }

  public initPlayer() {
		shaka.polyfill.installAll();
		if (shaka.Player.isBrowserSupported()) {
			console.log("Supported");
			var player = new shaka.Player(this.drmVideo.nativeElement);
      var clearKey = {}
      clearKey[this.kid] = this.value;
			player.configure({
				drm: {
					clearKeys: clearKey
				}
			})

			player.load(this.manifestUri).then(function () {
        console.log('The video has now been loaded!');
			}).catch((err) => console.log(err))
		} else {
			console.log("Not Supported");
		}
  }

  public getOnlineData() {
    if(this.network.type!='none'){ //if device online and there is no sd card/file
      this.manifestUri = 'https://s3.ap-south-1.amazonaws.com/media.test.qlsacademy/media/ckeditor/sample-video/dash/manifest.mpd'
      this.kid = '6699F0841763CDC672E43C5E676981CB'
      this.value = '1E9514A825A470DA65F30EA498B11E96'
      this.initPlayer();
    } else { //if sd does not exist nor is the device connected to the internet
      this.toast.create({
        message: "you are offline and there is no sd card so video will not play",
        duration: 5000
      }).present();
    }
  }

  public getOfflineData(){
    this.manifestUri = '';
    this.kid = '6699F0841763CDC672E43C5E676981CB';
    this.value = '1E9514A825A470DA65F30EA498B11E96';
    this.getOfflinePath();
  }

  public playVideo() {
    let video = this.drmVideo.nativeElement;
    video.play();
  }

  public pauseVideo(){
    let video = this.drmVideo.nativeElement;
    video.pause();
  }

  ngAfterViewInit(){
    setTimeout( ()=>{
        this.getOfflineData() //always start with offline data
    }, 1000)
  }

}
