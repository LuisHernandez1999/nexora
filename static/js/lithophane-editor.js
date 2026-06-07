/* Faça meu Lithophane — recorte (pan + zoom) no canvas + geração 3D + toggle de luz.
   Vanilla puro (sem framework): DOM + canvas + fetch. */
(function () {
  "use strict";

  var canvas = document.getElementById("litho-canvas");
  if (!canvas) return; // só roda na página do editor

  var ctx = canvas.getContext("2d");
  var fileInput = document.getElementById("litho-file");
  var btnInverter = document.getElementById("btn-inverter");
  var btnReset = document.getElementById("btn-reset");
  var btnGerar = document.getElementById("btn-gerar");
  var btnRefazer = document.getElementById("btn-refazer");
  var btnLuz = document.getElementById("btn-luz");
  var btnLuzLabel = document.getElementById("btn-luz-label");
  var btnStl = document.getElementById("btn-stl");
  var orderForm = document.getElementById("litho-order-form");
  var actions = document.getElementById("litho-actions");
  var viewerWrap = document.getElementById("litho-viewer-wrap");
  var cropWrap = document.getElementById("litho-crop");
  var empty = document.getElementById("litho-empty");
  var hint = document.getElementById("litho-hint");
  var sliderZoom = document.getElementById("litho-zoom");
  var sliderBrilho = document.getElementById("litho-brightness");

  // estado do recorte
  var imgOriginal = null;
  var inverter = false;
  var luzAtiva = false;
  var zoom = 100, panX = 0, panY = 0;

  // ---- liga os outputs dos sliders (e re-render quando afeta o preview) ----
  [["litho-size", "out-size"], ["litho-thickness", "out-thickness"],
   ["litho-brightness", "out-brightness"], ["litho-zoom", "out-zoom"]]
    .forEach(function (par) {
      var s = document.getElementById(par[0]);
      var o = document.getElementById(par[1]);
      if (!s || !o) return;
      s.addEventListener("input", function () {
        o.textContent = s.value;
        if (par[0] === "litho-brightness" || par[0] === "litho-zoom") {
          if (par[0] === "litho-zoom") zoom = +s.value;
          _render();
        }
      });
    });

  // ---- desenha a foto recortada (cover + zoom + pan) com filtros ----
  function _render() {
    if (!imgOriginal) return;
    var cw = canvas.width, ch = canvas.height;
    var iw = imgOriginal.width, ih = imgOriginal.height;
    var cover = Math.max(cw / iw, ch / ih);   // preenche o quadrado
    var s = cover * (zoom / 100);
    var dw = iw * s, dh = ih * s;
    var dx = (cw - dw) / 2 + panX;
    var dy = (ch - dh) / 2 + panY;
    var b = sliderBrilho ? sliderBrilho.value : 100;

    ctx.clearRect(0, 0, cw, ch);
    ctx.filter = "brightness(" + b + "%) grayscale(100%)";
    ctx.drawImage(imgOriginal, dx, dy, dw, dh);
    ctx.filter = "none";
    if (inverter) {
      var id = ctx.getImageData(0, 0, cw, ch);
      for (var i = 0; i < id.data.length; i += 4) {
        id.data[i] = 255 - id.data[i];
        id.data[i + 1] = 255 - id.data[i + 1];
        id.data[i + 2] = 255 - id.data[i + 2];
      }
      ctx.putImageData(id, 0, 0);
    }
  }

  function _reset() {
    zoom = 100; panX = 0; panY = 0;
    if (sliderZoom) { sliderZoom.value = 100; document.getElementById("out-zoom").textContent = "100"; }
    _render();
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
        if (hint) hint.style.display = "";
        _reset();
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
  if (btnReset) btnReset.addEventListener("click", _reset);

  // ---- arrastar para reposicionar (pan) ----
  var arrastando = false, lastX = 0, lastY = 0;
  function _pt(e) { return e.touches ? e.touches[0] : e; }
  canvas.addEventListener("pointerdown", function (e) {
    if (!imgOriginal) return;
    arrastando = true; lastX = e.clientX; lastY = e.clientY;
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = "grabbing";
  });
  canvas.addEventListener("pointermove", function (e) {
    if (!arrastando) return;
    var rect = canvas.getBoundingClientRect();
    var fx = canvas.width / rect.width;   // escala tela -> canvas
    panX += (e.clientX - lastX) * fx;
    panY += (e.clientY - lastY) * fx;
    lastX = e.clientX; lastY = e.clientY;
    _render();
  });
  function _soltar() { arrastando = false; canvas.style.cursor = "grab"; }
  canvas.addEventListener("pointerup", _soltar);
  canvas.addEventListener("pointercancel", _soltar);

  // ---- gerar o 3D no servidor ----
  function _csrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }

  async function _gerar() {
    if (!imgOriginal) { alert("Envie uma foto primeiro."); return; }
    var formatoEl = document.querySelector('input[name="formato"]:checked');
    var formato = formatoEl ? formatoEl.value : "placa";
    var dataURL = canvas.toDataURL("image/png");  // só o recorte visível
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

  // ---- volta do viewer para a edição ----
  if (btnRefazer) btnRefazer.addEventListener("click", function () {
    viewerWrap.hidden = true;
    if (cropWrap) cropWrap.style.display = "";
    actions.hidden = true;
    btnLuz.hidden = true;
  });

  // ---- troca o recorte pelo model-viewer ----
  function _mostrarViewer(data) {
    if (cropWrap) cropWrap.style.display = "none";
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
