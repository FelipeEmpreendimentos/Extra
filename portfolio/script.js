const header=document.querySelector('.site-header');
const menuToggle=document.querySelector('.menu-toggle');
const mobileMenu=document.querySelector('#mobile-menu');
const progressBar=document.querySelector('.scroll-progress span');
const backTop=document.querySelector('.back-top');
const yearNode=document.querySelector('#current-year');
const copyStatus=document.querySelector('#copy-status');

if(yearNode) yearNode.textContent=new Date().getFullYear();

const previewMockups=[
  {brand:'ALMEIDA & VASCONCELOS',kicker:'ADVOCACIA ESTRATÉGICA',title:'Clareza jurídica para decisões que movem o futuro.',action:'Solicitar atendimento ↗',image:'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1400&q=84',accent:'#e1bf78',overlay:'linear-gradient(90deg,rgba(5,8,11,.98) 0%,rgba(5,8,11,.90) 47%,rgba(5,8,11,.30) 100%)',className:'preview-dark'},
  {brand:'LUME ODONTOLOGIA',kicker:'ODONTOLOGIA CONTEMPORÂNEA',title:'Seu sorriso merece cuidado com leveza e precisão.',action:'Agendar avaliação ↗',image:'https://images.unsplash.com/photo-1606811971618-4486d14f3f99?auto=format&fit=crop&w=1400&q=86',accent:'#0e6f68',overlay:'linear-gradient(90deg,rgba(244,251,249,.99) 0%,rgba(244,251,249,.94) 49%,rgba(244,251,249,.16) 100%)',className:'preview-light'},
  {brand:'VÉRTICE IMÓVEIS',kicker:'CURADORIA IMOBILIÁRIA',title:'Lugares que combinam com o próximo capítulo.',action:'Explorar imóveis ↗',image:'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=86',accent:'#d38a62',overlay:'linear-gradient(90deg,rgba(20,21,20,.96) 0%,rgba(20,21,20,.78) 46%,rgba(20,21,20,.18) 100%)',className:'preview-dark'},
  {brand:'PONTA DE TORQUE',kicker:'GARAGE · SERVIÇOS AUTOMOTIVOS',title:'Seu carro em dia, sem surpresa e sem enrolação.',action:'Pedir orçamento ↗',image:'https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&w=1400&q=86',accent:'#ef7d32',overlay:'linear-gradient(90deg,rgba(8,10,12,.98) 0%,rgba(8,10,12,.84) 49%,rgba(8,10,12,.22) 100%)',className:'preview-dark'},
  {brand:'NEXO CONTÁBIL',kicker:'CONTABILIDADE CONSULTIVA',title:'Menos burocracia. Mais visão para o negócio.',action:'Falar com um especialista ↗',image:'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=86',accent:'#38c6a3',overlay:'linear-gradient(90deg,rgba(8,28,38,.98) 0%,rgba(8,28,38,.89) 48%,rgba(8,28,38,.24) 100%)',className:'preview-dark'},
  {brand:'NÍTIDO AUTO CARE',kicker:'ESTÉTICA AUTOMOTIVA',title:'Seu carro merece mais do que uma lavagem.',action:'Agendar cuidado ↗',image:'https://images.unsplash.com/photo-1607860108855-64acf2078ed9?auto=format&fit=crop&w=1400&q=86',accent:'#b8ff3d',overlay:'linear-gradient(90deg,rgba(5,8,9,.98) 0%,rgba(5,8,9,.82) 49%,rgba(5,8,9,.20) 100%)',className:'preview-dark'}
];

const previewStyles=document.createElement('style');
previewStyles.textContent=`
  .project-preview{display:flex;flex-direction:column}
  .iframe-stage.static-preview{position:relative;flex:1;height:auto!important;min-height:326px;overflow:hidden;background-size:cover;background-position:center;isolation:isolate}
  .project-wide .iframe-stage.static-preview{min-height:466px}
  .preview-mock{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:42px 44px;z-index:1}
  .project-wide .preview-mock{padding:58px 64px}
  .preview-mock.preview-dark{color:#fff}
  .preview-mock.preview-light{color:#113c39}
  .preview-mock-brand{display:flex;align-items:center;gap:10px;font:800 .68rem/1 var(--title);letter-spacing:.16em;text-transform:uppercase}
  .preview-mock-brand:before{content:"";width:28px;height:2px;background:var(--preview-accent)}
  .preview-mock-kicker{margin-top:34px;font-size:.62rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--preview-accent)}
  .preview-mock-title{max-width:430px;margin-top:12px;font:800 clamp(1.7rem,3vw,3rem)/1.02 var(--title);letter-spacing:-.045em}
  .project-wide .preview-mock-title{max-width:560px;font-size:clamp(2.3rem,4vw,4.3rem)}
  .preview-mock-action{display:inline-flex;align-self:flex-start;margin-top:24px;padding:10px 14px;background:var(--preview-accent);color:#0c1111;font-size:.68rem;font-weight:800}
  .preview-mock.preview-light .preview-mock-action{color:#fff}
  .preview-mock-deco{position:absolute;right:7%;bottom:9%;width:88px;height:88px;border:1px solid color-mix(in srgb,var(--preview-accent) 55%,transparent);border-radius:50%;opacity:.72}
  .preview-mock-deco:after{content:"";position:absolute;width:8px;height:8px;border-radius:50%;background:var(--preview-accent);top:12px;right:8px;box-shadow:0 0 18px var(--preview-accent)}
  @media(max-width:1080px){.project-wide .iframe-stage.static-preview{min-height:356px}.preview-mock,.project-wide .preview-mock{padding:34px}.project-wide .preview-mock-title{font-size:2.7rem}}
  @media(max-width:620px){.iframe-stage.static-preview,.project-wide .iframe-stage.static-preview{min-height:270px}.preview-mock,.project-wide .preview-mock{padding:26px}.preview-mock-kicker{margin-top:24px}.preview-mock-title,.project-wide .preview-mock-title{font-size:1.8rem;max-width:85%}.preview-mock-deco{width:62px;height:62px}}
`;
document.head.appendChild(previewStyles);

document.querySelectorAll('.iframe-stage').forEach((stage,index)=>{
  const data=previewMockups[index];
  if(!data) return;
  stage.querySelector('iframe')?.remove();
  stage.classList.add('static-preview');
  stage.style.backgroundImage=`${data.overlay}, url("${data.image}")`;
  stage.style.backgroundSize='cover';
  stage.style.backgroundPosition=index===1?'center right':'center';
  stage.innerHTML=`<div class="preview-mock ${data.className}" style="--preview-accent:${data.accent}"><div class="preview-mock-brand">${data.brand}</div><div class="preview-mock-kicker">${data.kicker}</div><div class="preview-mock-title">${data.title}</div><span class="preview-mock-action">${data.action}</span><span class="preview-mock-deco" aria-hidden="true"></span></div>`;
});

const updateScrollUI=()=>{
  const y=window.scrollY;
  header?.classList.toggle('scrolled',y>28);
  backTop?.classList.toggle('visible',y>700);
  if(progressBar){const doc=document.documentElement;const max=doc.scrollHeight-doc.clientHeight;progressBar.style.width=max>0?`${Math.min((y/max)*100,100)}%`:'0%';}
};
updateScrollUI();
window.addEventListener('scroll',updateScrollUI,{passive:true});

const closeMenu=()=>{
  if(!menuToggle||!mobileMenu) return;
  menuToggle.setAttribute('aria-expanded','false');
  menuToggle.setAttribute('aria-label','Abrir menu');
  mobileMenu.hidden=true;
  document.body.classList.remove('menu-open');
};
menuToggle?.addEventListener('click',()=>{
  if(!mobileMenu) return;
  const open=menuToggle.getAttribute('aria-expanded')==='true';
  menuToggle.setAttribute('aria-expanded',String(!open));
  menuToggle.setAttribute('aria-label',open?'Abrir menu':'Fechar menu');
  mobileMenu.hidden=open;
  document.body.classList.toggle('menu-open',!open);
});
document.querySelectorAll('#mobile-menu a').forEach(link=>link.addEventListener('click',closeMenu));
window.addEventListener('resize',()=>{if(window.innerWidth>1080) closeMenu();});
window.addEventListener('keydown',event=>{if(event.key==='Escape') closeMenu();});
backTop?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));

const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const revealElements=document.querySelectorAll('.reveal');
if(reducedMotion||!('IntersectionObserver' in window)){
  revealElements.forEach(el=>el.classList.add('in-view'));
}else{
  const revealObserver=new IntersectionObserver((entries,observer)=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');observer.unobserve(entry.target);}});},{threshold:.1,rootMargin:'0px 0px -38px'});
  revealElements.forEach((el,index)=>{el.style.transitionDelay=`${Math.min(index%4,3)*45}ms`;revealObserver.observe(el);});
}

const navLinks=[...document.querySelectorAll('.desktop-nav a[href^="#"]')];
const navSections=navLinks.map(link=>document.querySelector(link.getAttribute('href'))).filter(Boolean);
if('IntersectionObserver' in window&&navSections.length){
  const navObserver=new IntersectionObserver(entries=>{
    const visible=entries.filter(entry=>entry.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if(!visible) return;
    navLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')===`#${visible.target.id}`));
  },{rootMargin:'-28% 0px -58% 0px',threshold:[0,.05,.2,.5]});
  navSections.forEach(section=>navObserver.observe(section));
}

const message='Olá! Vi seu portfólio de sites e gostaria de conversar sobre a criação de um site para minha empresa.';
const copyMessage=async(button)=>{
  try{
    await navigator.clipboard.writeText(message);
    const original=button.textContent;
    button.textContent='Mensagem copiada ✓';
    if(copyStatus) copyStatus.textContent='Mensagem copiada. Agora é só colar no WhatsApp, Instagram ou outro canal de contato.';
    setTimeout(()=>{button.textContent=original;if(copyStatus) copyStatus.textContent='';},2600);
  }catch{
    if(copyStatus) copyStatus.textContent=`Copie esta mensagem: ${message}`;
  }
};
document.querySelectorAll('.copy-message').forEach(button=>button.addEventListener('click',()=>copyMessage(button)));