/* Faça meu Lithophane — editor 2D no canvas + geração 3D + toggle de luz.
   Vanilla puro (sem framework): DOM + canvas + fetch. */
(function () {
  "use strict";

  var canvas = document.getElementById("litho-canvas");
  if (!canvas) return; // só roda na página do editor

  var ctx = canvas.getContext("2d");
  var fileInput = document.getElementById("litho-file");
  var btnInverter = document.getElementById("btn-inverter");
  var btnGerar = document.getElementById("btn-gerar");
  var btnLuz = document.getElementById("btn-luz");
  var btnLuzLabel = document.getElementById("btn-luz-label");
  var btnStl = document.getElementById("btn-stl");
  var orderForm = document.getElementById("litho-order-form");
  var actions = document.getElementById("litho-actions");
  var viewerWrap = document.getElementById("litho-viewer-wrap");
  var empty = document.getElementById("litho-empty");
  var sliderBrilho = document.getElementById("litho-brightness");

  var imgOriginal = null;
  var inverter = false;
  var luzAtiva = false;

  // ---- liga os outputs dos sliders ----
  [["litho-size", "out-size"], ["litho-thickness", "out-thickness"], ["litho-brightness", "out-brightness"]]
    .forEach(function (par) {
      var s = document.getElementById(par[0]);
      var o = document.getElementById(par[1]);
      if (s && o) s.addEventListener("input", function () {
        o.textContent = s.value;
        if (par[0] === "litho-brightness") _render();
      });
    });

  // ---- desenha a foto no canvas com filtros (preview do relevo) ----
  function _render() {
    if (!imgOriginal) return;
    var b = sliderBrilho ? sliderBrilho.value : 100;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.filter = "brightness(" + b + "%) grayscale(100%)";
    ctx.drawImage(imgOriginal, 0, 0, canvas.width, canvas.height);
    ctx.filter = "none";
    if (inverter) {
      var id = ctx.getImageData(0, 0, canvas.width, canvas.height);
      for (var i = 0; i < id.data.length; i += 4) {
        id.data[i] = 255 - id.data[i];
        id.data[i + 1] = 255 - id.data[i + 1];
        id.data[i + 2] = 255 - id.data[i + 2];
      }
      ctx.putImageData(id, 0, 0);
    }
  }

  // ---- upload ----
  if (fileInput) fileInput.addEventListener("change", function (e) {
    var file = e.target.files && e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function (ev) {
      var img = new Image();
      img.onload = function () {
        imgOriginal = img;
        if (empty) empty.hidden = true;
        _render();
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  });

  if (btnInverter) btnInverter.addEventListener("click", function () {
    inverter = !inverter;
    btnInverter.classList.toggle("luz-ativa", inverter);
    _render();
  });

  // ---- gerar o 3D no servidor ----
  function _csrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }

  async function _gerar() {
    if (!imgOriginal) { alert("Envie uma foto primeiro."); return; }
    var formatoEl = document.querySelector('input[name="formato"]:checked');
    var formato = formatoEl ? formatoEl.value : "placa";
    var dataURL = canvas.toDataURL("image/png");
    var fd = new FormData();
    fd.append("imagem", dataURL);
    fd.append("formato", formato);
    fd.append("largura_mm", document.getElementById("litho-size").value);
    fd.append("espessura_max_mm", document.getElementById("litho-thickness").value);

    btnGerar.disabled = true;
    btnGerar.textContent = "Gerando…";
    try {
      var resp = await fetch("/lithophane/gerar/", {
        method: "POST",
        headers: { "X-CSRFToken": _csrf() },
        body: fd
      });
      var data = await resp.json();
      if (!data.ok) throw new Error(data.erro || "Falha ao gerar.");
      _mostrarViewer(data);
    } catch (err) {
      alert(err.message);
    } finally {
      btnGerar.disabled = false;
      btnGerar.innerHTML = '<svg class="icon"><use href="#i-spark"></use></svg> Gerar 3D';
    }
  }
  if (btnGerar) btnGerar.addEventListener("click", _gerar);

  // ---- troca o canvas pelo model-viewer ----
  function _mostrarViewer(data) {
    canvas.style.display = "none";
    if (empty) empty.hidden = true;

    var viewer = document.getElementById("litho-viewer");
    if (!viewer) {
      viewer = document.createElement("model-viewer");
      viewer.id = "litho-viewer";
      viewer.setAttribute("camera-controls", "");
      viewer.setAttribute("auto-rotate", "");
      viewer.setAttribute("touch-action", "pan-y");
      viewer.setAttribute("shadow-intensity", "1");
      viewerWrap.appendChild(viewer);
    }
    viewer.setAttribute("src", data.glb_url);
    if (data.image_url) viewer.setAttribute("poster", data.image_url);
    viewer.setAttribute("exposure", "1.0");
    viewerWrap.hidden = false;

    // botões pós-geração
    btnStl.setAttribute("href", data.stl_url);
    orderForm.setAttribute("action", "/carrinho/lithophane/adicionar/" + data.draft_id + "/");
    actions.hidden = false;
    btnLuz.hidden = false;
    luzAtiva = false;
    btnLuz.classList.remove("luz-ativa");
    if (btnLuzLabel) btnLuzLabel.textContent = "Com luz";
  }

  // ---- toggle de luz (efeito emissivo: a foto "acende") ----
  if (btnLuz) btnLuz.addEventListener("click", function () {
    var viewer = document.getElementById("litho-viewer");
    if (!viewer || !viewer.model) return;
    var mat = viewer.model.materials[0];
    luzAtiva = !luzAtiva;
    if (luzAtiva) {
      mat.setEmissiveFactor([1.0, 0.9, 0.7]);
      mat.setEmissiveStrength(4.0);
      viewer.setAttribute("exposure", "0.4");
      viewer.setAttribute("shadow-intensity", "0");
    } else {
      mat.setEmissiveFactor([0, 0, 0]);
      mat.setEmissiveStrength(0);
      viewer.setAttribute("exposure", "1.0");
      viewer.setAttribute("shadow-intensity", "1");
    }
    btnLuz.classList.toggle("luz-ativa", luzAtiva);
    if (btnLuzLabel) btnLuzLabel.textContent = luzAtiva ? "Sem luz" : "Com luz";
  });
})();
