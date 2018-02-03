/*global $*/


$( document ).ready(function() {
    $('#flash').css({ 'opacity' : 1 });
});

$( document ).click(function() {
  $('#flash').css({ 'opacity' : 0 });
});

var serverTime = new Date();
var countdown = serverTime;
var hidden = false;

function updateTime() {
    /// Increment serverTime by 1 second and update the html for '#time'
    serverTime = new Date(serverTime.getTime() + 1000);
    $('#time').text(serverTime.toLocaleString()+" PST");
    if (((serverTime.getTime()-countdown.getTime())/1000) > 10 && !hidden){
        hidden = true;
        $('#flash').css({ 'opacity' : 0 });
    }
}
$(function() {
    updateTime();
    setInterval(updateTime, 1000);
});