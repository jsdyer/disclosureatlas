import {matches} from './model.mjs';

const form = document.querySelector('[data-filter]');
if (form) {
  const cards = [...document.querySelectorAll('[data-case]')];
  const status = document.querySelector('[data-status]');
  const {query, kind, region} = form.elements;
  function display() {
    let count = 0;
    for (const card of cards) {
      card.hidden = !matches(card.dataset, {query: query.value, kind: kind.value, region: region.value});
      if (!card.hidden) count++;
    }
    status.textContent = count ? `${count} ${count === 1 ? 'casefile' : 'casefiles'} shown` : 'No matching casefiles. Clear the filters or try another search.';
    form.querySelector('button').hidden = !(query.value || kind.value || region.value);
  }
  function restore() {
    const params = new URLSearchParams(location.hash.slice(1));
    query.value = params.get('q') || '';
    kind.value = params.get('type') || '';
    region.value = params.get('place') || '';
    display();
  }
  function update() {
    const params = new URLSearchParams();
    for (const [key, value] of [['q',query.value],['type',kind.value],['place',region.value]]) {
      if (value) params.set(key, value);
    }
    history.replaceState(null, '', location.pathname + location.search + (params.size ? '#' + params : ''));
    display();
  }
  form.hidden = false;
  form.addEventListener('input', update);
  form.addEventListener('submit', event => {event.preventDefault(); update()});
  form.addEventListener('reset', event => {
    event.preventDefault();
    query.value = kind.value = region.value = '';
    update();
    query.focus();
  });
  window.addEventListener('hashchange', restore);
  restore();
}
