/*
comments

8-12-2016
geschreven door Ties Noordhuis

*/
/*variable*/

var n = 0;
var fotos = ["huis1.png", "huis2.png", "huis3.png", "P8302462.JPG", "P8302463.JPG", "P8302464.JPG", "P8302465.JPG"]
var fotosDescription = ["vooraanzicht", "vooraanzicht", "vooraanzicht", "uitzicht balkon", "uitzicht balkon", "uitzicht balkon", "balkon"]

function setGalerijStyle(n) {
  if (n == 1) {
    document.getElementById('myCarousel').style.display = "block";
    document.getElementById('setGalerijStyleSlideshow').className = "btn btn-default btnFotos active";
    document.getElementById('myGrid').style.display = "none";
    document.getElementById('setGalerijStyleGrid').className = "btn btn-default btnFotos";
  }
  else if (n == 2) {
    document.getElementById('myCarousel').style.display = "none";
    document.getElementById('setGalerijStyleSlideshow').className = "btn btn-default btnFotos";
    document.getElementById('myGrid').style.display = "block";
    document.getElementById('setGalerijStyleGrid').className = "btn btn-default btnFotos active";
    setFotosGrid()
  }
  else {
    window.alert("fout in setGalerijStyle");
  }
}

function setFotosGrid(){
  for (var i = 0; i < fotos.length; i++) {
    document.getElementById("myGrid").innerHTML += "test" + i + "test";
  }
  window.alert("setFotosGrid");
}
