(function () {
  var form = document.getElementById("formAdd");
  if (!form) return;
  form.addEventListener("submit", function () {
    var boton = form.querySelector(".boton");
    if (boton) boton.disabled = true;
  });
})();