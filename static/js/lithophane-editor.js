/* Faça meu Lithophane — cropper (moldura com proporção) + geração 3D + toggle de luz.
   Vanilla puro: DOM + canvas + fetch. */
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
  var imgEl = document.getElementById("litho-img");
  var cropBox = document.getElementById("crop-box");
  var ratios = document.getElementById("litho-ratios");
  var empty = document.getElementById("litho-empty");
  var hint = document.getElementById("litho-hint");
  var sliderBrilho = document.getElementById("litho-brightness");

  var imgPronta = false;
  var aspecto = 1;            // largura/altura da moldura
  var inverter = false;
  var luzAtiva = false;
  var box = { x: 0, y: 0, w: 10, h: 10 };  // moldura em px de tela (relativo à imagem)

  function _imgRect() { return { w: imgEl.offsetWidth, h: imgEl.offsetHeight }; }

  function _aplicarFiltroPreview() {
    var b = sliderBrilho ? sliderBrilho.value : 100;
    var f = "grayscale(100%) brightness(" + b + "%)" + (inverter ? " invert(100%)" : "");
    imgEl.style.filter = f;
  }

  function _desenharBox() {
    cropBox.style.left = box.x + "px";
    cropBox.style.top = box.y + "px";
    cropBox.style.width = box.w + "px";
    cropBox.style.height = box.h + "px";
  }

  // centraliza a moldura no maior tamanho que cabe na imagem para o aspecto atual
  function _ajustarBox() {
    var r = _imgRect();
    if (!r.w) return;
    var maxW = r.w * 0.92, maxH = r.h * 0.92;
    var w, h;
    if (maxW / maxH > aspecto) { h = maxH; w = h * aspecto; }
    else { w = maxW; h = w / aspecto; }
    box.w = w; box.h = h;
    box.x = (r.w - w) / 2;
    box.y = (r.h - h) / 2;
    _desenharBox();
  }

  // ---- upload ----
  if (fileInput) fileInput.addEventListener("change", function (e) {
    var file = e.target.files && e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function (ev) {
      imgEl.onload = function () {
        imgPronta = true;
        imgEl.hidden = false;
        if (empty) empty.hidden = true;
        cropBox.style.display = "block";
        if (hint) hint.hidden = false;
        _aplicarFiltroPreview();
        _ajustarBox();
      };
      imgEl.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  });

  if (sliderBrilho) sliderBrilho.addEventListener("input", function () {
    var o = document.getElementById("out-brightness");
    if (o) o.textContent = sliderBrilho.value;
    _aplicarFiltroPreview();
  });
  if (btnInverter) btnInverter.addEventListener("click", function () {
    inverter = !inverter;
    btnInverter.classList.toggle("luz-ativa", inverter);
    _aplicarFiltroPreview();
  });
  if (btnReset) btnReset.addEventListener("click", _ajustarBox);

  // ---- proporção ----
  if (ratios) ratios.addEventListener("click", function (e) {
    var b = e.target.closest(".ratio");
    if (!b) return;
    aspecto = parseFloat(b.getAttribute("data-ratio")) || 1;
    Array.prototype.forEach.call(ratios.querySelectorAll(".ratio"), function (x) { x.classList.remove("is-on"); });
    b.classList.add("is-on");
    if (imgPronta) _ajustarBox();
  });

  // ---- mover / redimensionar a moldura ----
  var modo = null, alvo = null, start = null;
  function _xy(e) {
    var r = cropWrap.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }
  function _clamp() {
    var r = _imgRect();
    box.w = Math.max(40, Math.min(box.w, r.w));
    box.h = box.w / aspecto;
    if (box.h > r.h) { box.h = r.h; box.w = box.h * aspecto; }
    box.x = Math.max(0, Math.min(box.x, r.w - box.w));
    box.y = Math.max(0, Math.min(box.y, r.h - box.h));
  }
  cropBox.addEventListener("pointerdown", function (e) {
    if (!imgPronta) return;
    e.preventDefault();
    cropBox.setPointerCapture(e.pointerId);
    var h = e.target.classList && e.target.classList.contains("crop-h") ? e.target : null;
    modo = h ? "resize" : "move";
    alvo = h ? (h.className.split(" ").pop()) : null;
    start = { p: _xy(e), box: Object.assign({}, box) };
  });
  cropBox.addEventListener("pointermove", function (e) {
    if (!modo) return;
    var p = _xy(e);
    var dx = p.x - start.p.x, dy = p.y - start.p.y;
    if (modo === "move") {
      box.x = start.box.x + dx;
      box.y = start.box.y + dy;
    } else {
      // canto fixo = oposto ao arrastado; mantém aspecto pela largura
      var right = start.box.x + start.box.w, bottom = start.box.y + start.box.h;
      var nw = start.box.w + (alvo === "tr" || alvo === "br" ? dx : -dx);
      nw = Math.max(40, nw);
      var nh = nw / aspecto;
      if (alvo === "tl") { box.x = right - nw; box.y = bottom - nh; }
      else if (alvo === "tr") { box.x = start.box.x; box.y = bottom - nh; }
      else if (alvo === "bl") { box.x = right - nw; box.y = start.box.y; }
      else { box.x = start.box.x; box.y = start.box.y; }
      box.w = nw; box.h = nh;
    }
    _clamp();
    _desenharBox();
  });
  function _fim() { modo = null; alvo = null; }
  cropBox.addEventListener("pointerup", _fim);
  cropBox.addEventListener("pointercancel", _fim);

  // ---- extrai o recorte para um dataURL (com filtros) ----
  function _recorteDataURL() {
    var r = _imgRect();
    var escala = imgEl.naturalWidth / r.w;     // tela -> pixels reais da foto
    var sx = box.x * escala, sy = box.y * escala;
    var sw = box.w * escala, sh = box.h * escala;
    var saida = 700;                            // maior lado do recorte exportado
    var ow = aspecto >= 1 ? saida : Math.round(saida * aspecto);
    var oh = aspecto >= 1 ? Math.round(saida / aspecto) : saida;
    canvas.width = ow; canvas.height = oh;
    var b = sliderBrilho ? sliderBrilho.value : 100;
    ctx.filter = "grayscale(100%) brightness(" + b + "%)" + (inverter ? " invert(100%)" : "");
    ctx.drawImage(imgEl, sx, sy, sw, sh, 0, 0, ow, oh);
    ctx.filter = "none";
    return canvas.toDataURL("image/png");
  }

  // ---- gerar o 3D no servidor ----
  function _csrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }
  async function _gerar() {
    if (!imgPronta) { alert("Envie uma foto primeiro."); return; }
    var formatoEl = document.querySelector('input[name="formato"]:checked');
    var formato = formatoEl ? formatoEl.value : "placa";
    var fd = new FormData();
    fd.append("imagem", _recorteDataURL());
    fd.append("formato", formato);
    fd.append("largura_mm", document.getElementById("litho-size").value);
    fd.append("espessura_max_mm", document.getElementById("litho-thickness").value);
    btnGerar.disabled = true; btnGerar.textContent = "Gerando…";
    try {
      var resp = await fetch("/lithophane/gerar/", {
        method: "POST", headers: { "X-CSRFToken": _csrf() }, body: fd
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

  // re-ajusta a moldura se a janela mudar de tamanho
  window.addEventListener("resize", function () { if (imgPronta) _ajustarBox(); });
})();
