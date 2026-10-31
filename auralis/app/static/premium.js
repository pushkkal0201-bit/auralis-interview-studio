/* Page navigation and accessible interaction enhancements. */
'use strict';
document.addEventListener('DOMContentLoaded',()=>{
  const $=id=>document.getElementById(id);
  const sample=$('hero-sample');
  sample?.addEventListener('click',()=>{
    $('sample').click();
    $('setup-form').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});
    $('cv').focus({preventScroll:true});
  });
  $('empty-setup')?.addEventListener('click',()=>document.querySelector('.nav[data-view="setup"]')?.click());
  const navs=[...document.querySelectorAll('.nav')];
  const update=()=>{
    for(const nav of navs){
      const active=nav.classList.contains('active');
      if(active){nav.setAttribute('aria-current','page');$('view-label').textContent=nav.querySelector('span:last-child')?.textContent.trim() || nav.textContent.trim();}
      else nav.removeAttribute('aria-current');
    }
  };
  const observer=new MutationObserver(update);
  navs.forEach(nav=>observer.observe(nav,{attributes:true,attributeFilter:['class']}));
  update();
  // Advanced tools may be deep-linked without making every setup intimidating.
  const adv=$('advanced-tools');
  for(const field of ['repo-file','repo-url','incident-select','rea-file']) {
    const node=$(field);
    node?.addEventListener('focus',()=>{if(adv)adv.open=true});
  }
});
