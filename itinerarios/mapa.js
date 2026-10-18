(function () {
  var D = window.YOKA_MAP;
  if (!window.L || !D || !D.markers.length) { var m = document.getElementById('map'); if (m && D && !D.markers.length) m.remove(); return; }
  var map = L.map('map', { scrollWheelZoom: false });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap' }).addTo(map);
  var groups = {}, all = [];
  D.markers.forEach(function (m) {
    var icon = L.divIcon({ className: '', html: '<div class="num" style="background:' + D.colors[m.day % D.colors.length] + '">' + m.n + '</div>', iconSize: [24, 24], iconAnchor: [12, 12] });
    var mk = L.marker([m.lat, m.lng], { icon: icon }).bindPopup(function () {
      var day = document.documentElement.lang === 'en' ? 'Day ' : 'Día ';
      var nm = document.documentElement.lang === 'en' ? (m.name_en || m.name) : m.name;
      return '<strong>' + nm + '</strong><br>' + day + (m.day + 1) + (m.time ? ' · ' + m.time : '');
    });
    (groups[m.day] = groups[m.day] || []).push(mk); all.push(mk); mk.addTo(map);
  });
  var fitAll = function () { map.fitBounds(L.featureGroup(all).getBounds(), { padding: [24, 24], maxZoom: 14 }); };
  fitAll();
  var chips = document.querySelectorAll('#legend .chip'), active = null;
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      var d = +c.dataset.day;
      chips.forEach(function (x) { x.classList.remove('on'); });
      if (active === d) { active = null; fitAll(); return; }
      active = d; c.classList.add('on');
      map.fitBounds(L.featureGroup(groups[d]).getBounds(), { padding: [30, 30], maxZoom: 15 });
    });
  });
})();
