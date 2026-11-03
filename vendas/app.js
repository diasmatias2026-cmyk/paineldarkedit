'use strict';
const captions={lote:'Todos os seus vídeos. Uma visão do lote.',ajuste:'Cada cena com o seu próprio enquadramento.',exportacao:'O processamento acontece no seu computador.'};
const frame=document.querySelector('.editor-frame');
document.querySelectorAll('[data-feature]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-feature]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button))});frame.dataset.focus=button.dataset.feature;document.querySelector('#featureCaption').textContent=captions[button.dataset.feature]}));
const zoom=document.querySelector('#frameZoom');zoom.addEventListener('input',()=>{document.querySelector('#demoScene').style.setProperty('--zoom',Number(zoom.value)/100);document.querySelector('#zoomValue').textContent=zoom.value+'%'});

document.addEventListener('keydown',()=>document.documentElement.classList.add('keyboard-input'));document.addEventListener('pointerdown',()=>document.documentElement.classList.remove('keyboard-input'));
