/*global $*/


$( document ).ready(function() {
    $('#flash').css({ 'opacity' : 1 });
});

$( document ).click(function() {
  $('#flash').css({ 'opacity' : 0 });
});

var serverTime = new Date();


function updateTime() {
    /// Increment serverTime by 1 second and update the html for '#time'
    serverTime = new Date(serverTime.getTime() + 1000);
    $('#time').text(serverTime.toLocaleString()+" PST");
}
$(function() {
    updateTime();
    setInterval(updateTime, 1000);
});