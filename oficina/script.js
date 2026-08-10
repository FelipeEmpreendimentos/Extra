const header=document.querySelector('.site-header');
const menuToggle=document.querySelector('.menu-toggle');
const mobileMenu=document.querySelector('#mobile-menu');
const backToTop=document.querySelector('.back-to-top');
const progressBar=document.querySelector('.scroll-progress span');
const yearNode=document.querySelector('#current-year');
const form=document.querySelector('#contact-form');
const formStatus=document.querySelector('#form-status');
const phoneInput=document.querySelector('#telefone');
const whatsappNumber='5546991331846';
const whatsappDisplay='(46) 99133-1846';

const migrateOwnerRefs=()=>{
  const oldHost='fedidinho.github.io';
  const newHost='felipeempreendimentos.github.io';
  const author=document.querySelector('meta[name="author"]');
  if(author) author.content='FelipeEmpreendimentos';
  document.querySelectorAll('[href]').forEach(el=>{const value=el.getAttribute('href');if(value?.includes(oldHost)) el.setAttribute('href',value.replaceAll(oldHost,newHost));});
  document.querySelectorAll('meta[content]').forEach(el=>{const value=el.getAttribute('content');if(value?.includes(oldHost)) el.setAttribute('content',value.replaceAll(oldHost,newHost));});
  document.querySelectorAll('script[type="application/ld+json"]').forEach(el=>{if(el.textContent.includes(oldHost)) el.textContent=el.textContent.replaceAll(oldHost,newHost);});
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let node;while((node=walker.nextNode())){if(node.nodeValue?.includes('Fedidinho')) node.nodeValue=node.nodeValue.replaceAll('Fedidinho','FelipeEmpreendimentos');}
};
migrateOwnerRefs();

const applyTestWhatsapp=()=>{
  document.querySelectorAll('a[href*="5541999999999"]').forEach(link=>{
    const href=link.getAttribute('href');
    if(href) link.setAttribute('href',href.replaceAll('5541999999999',whatsappNumber));
  });
  document.querySelectorAll('a[href="tel:+5541999999999"]').forEach(link=>link.setAttribute('href','tel:+5546991331846'));
  document.querySelectorAll('a').forEach(link=>{if(link.textContent.trim()==='(41) 99999-9999') link.textContent=whatsappDisplay;});
  document.querySelectorAll('script[type="application/ld+json"]').forEach(el=>{
    if(el.textContent.includes('+55-41-99999-9999')) el.textContent=el.textContent.replaceAll('+55-41-99999-9999','+55-46-99133-1846');
  });
};
applyTestWhatsapp();

if(yearNode) yearNode.textContent=new Date().getFullYear();

const serviceLabel=document.querySelector('label[for="servico"]');
if(serviceLabel) serviceLabel.textContent='Serviços';

const submitButton=form?.querySelector('button[type="submit"]');
if(submitButton) submitButton.textContent='Enviar solicitação pelo WhatsApp';
if(form && !form.querySelector('.whatsapp-form-note')){
  const note=document.createElement('small');
  note.className='whatsapp-form-note';
  note.textContent='Ao enviar, você será direcionado ao WhatsApp da oficina com as informações preenchidas para concluir o atendimento.';
  form.appendChild(note);
}

const updateScrollUI=()=>{
  const y=window.scrollY;
  header?.classList.toggle('scrolled',y>28);
  backToTop?.classList.toggle('visible',y>700);
  if(progressBar){
    const doc=document.documentElement;
    const max=doc.scrollHeight-doc.clientHeight;
    progressBar.style.width=max>0?`${Math.min((y/max)*100,100)}%`:'0%';
  }
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
backToTop?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));

const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const revealElements=document.querySelectorAll('.reveal');
if(reducedMotion||!('IntersectionObserver' in window)){
  revealElements.forEach(el=>el.classList.add('in-view'));
}else{
  const revealObserver=new IntersectionObserver((entries,observer)=>{
    entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('in-view');observer.unobserve(entry.target);}});
  },{threshold:.11,rootMargin:'0px 0px -38px'});
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

const counters=document.querySelectorAll('[data-counter]');
const animateCounter=element=>{
  const target=Number(element.dataset.counter||0);
  const suffix=element.dataset.suffix||'';
  const duration=1250;
  const start=performance.now();
  const tick=now=>{
    const progress=Math.min((now-start)/duration,1);
    const eased=1-Math.pow(1-progress,3);
    element.textContent=`${Math.floor(target*eased)}${suffix}`;
    if(progress<1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};
if('IntersectionObserver' in window&&!reducedMotion){
  const counterObserver=new IntersectionObserver((entries,observer)=>{entries.forEach(entry=>{if(entry.isIntersecting){animateCounter(entry.target);observer.unobserve(entry.target);}});},{threshold:.6});
  counters.forEach(counter=>counterObserver.observe(counter));
}else{counters.forEach(counter=>counter.textContent=`${counter.dataset.counter||0}${counter.dataset.suffix||''}`);}

document.querySelectorAll('.faq-item button').forEach(button=>{
  button.addEventListener('click',()=>{
    const answer=button.closest('.faq-item')?.querySelector('.faq-answer');
    if(!answer) return;
    const expanded=button.getAttribute('aria-expanded')==='true';
    document.querySelectorAll('.faq-item button[aria-expanded="true"]').forEach(openButton=>{
      if(openButton!==button){openButton.setAttribute('aria-expanded','false');const openAnswer=openButton.closest('.faq-item')?.querySelector('.faq-answer');if(openAnswer) openAnswer.hidden=true;}
    });
    button.setAttribute('aria-expanded',String(!expanded));
    answer.hidden=expanded;
  });
});

phoneInput?.addEventListener('input',()=>{
  const digits=phoneInput.value.replace(/\D/g,'').slice(0,11);
  let formatted=digits;
  if(digits.length>2) formatted=`(${digits.slice(0,2)}) ${digits.slice(2)}`;
  if(digits.length>7) formatted=`(${digits.slice(0,2)}) ${digits.slice(2,7)}-${digits.slice(7)}`;
  phoneInput.value=formatted;
});

form?.addEventListener('submit',event=>{
  event.preventDefault();
  if(!form.checkValidity()){
    form.reportValidity();
    if(formStatus) formStatus.textContent='Revise os campos obrigatórios antes de continuar.';
    return;
  }

  const data=new FormData(form);
  const nome=(data.get('nome')||'').toString().trim();
  const telefone=(data.get('telefone')||'').toString().trim();
  const veiculo=(data.get('veiculo')||'').toString().trim()||'Não informado';
  const servico=(data.get('servico')||'').toString().trim();
  const relato=(data.get('mensagem')||'').toString().trim();

  const message=[
    'Olá! Gostaria de solicitar um orçamento para meu veículo.',
    '',
    `*Nome:* ${nome}`,
    `*Telefone:* ${telefone}`,
    `*Veículo:* ${veiculo}`,
    `*Serviço:* ${servico}`,
    `*Relato:* ${relato}`
  ].join('\n');

  const url=`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
  if(formStatus) formStatus.textContent='Abrindo o WhatsApp com sua solicitação preenchida...';
  window.open(url,'_blank','noopener,noreferrer');
});