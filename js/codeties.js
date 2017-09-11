/*
comments

8-12-2016
geschreven door Ties Noordhuis

*/
/*variable*/

function modalImgSelector(n) {
  var divCarouselItem = document.getElementsByClassName("carousel-item");
  for (var i = 0; i < divCarouselItem.length; i++) {
    divCarouselItem[i].className = "carousel-item";
  }
  divCarouselItem[n].className += " active";
}
