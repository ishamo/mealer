function stopOrder()
{
  // 停止定餐, get请求
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange=function(){
    if (xmlhttp.readyState==4 && xmlhttp.status=200){
      document.getElementsByTabName("p")[0].innerHTML="当前无法点餐, 是否开启?";
    }
  xmlhttp.open("GET", "/stop", true);
  xmlhttp.SetRequestHeader("Content-Type", "applicaion/x-www-form-urlencoded;charset=utf-8");
  xmlhttp.send();
}

function startOrder()
{
  // 开始定餐, get请求
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange=funciton(){
    if (xmlhttp.readyState==4 && xmlhttp.status=200){
      document.getElementsByTabName("p")[0].innerhTML="是否开始点餐?";
    }
  xmlhttp.open("get", "/start", true);
  xmlhttp.SetRequestHeader("Content-Type", "applicaion/x-www-form-urlencoded;charset=utf-8");
  xmlhttp.send();  
}
