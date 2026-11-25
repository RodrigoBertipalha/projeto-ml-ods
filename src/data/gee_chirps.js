// CHIRPS — chuva acumulada no "ano PRODES" anterior ao rótulo
// Recorte Petrolina/Juazeiro (mesmo retângulo do MapBiomas e do PRODES).
// Banda chuva_t{T} = precipitação total (mm) de 1º/ago de T−2 a 31/jul de T−1,
// a mesma janela usada para os focos (decisão anti-vazamento).
// Rótulos T = 2017…2025 → 9 bandas.

var regiao = ee.Geometry.Rectangle([-40.97, -10.0, -39.84, -8.61]);
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').select('precipitation');

var bandas = [];
for (var t = 2017; t <= 2025; t++) {
  var inicio = ee.Date.fromYMD(t - 2, 8, 1);
  var fim = ee.Date.fromYMD(t - 1, 8, 1);  // filterDate exclui o fim → até 31/jul
  var total = chirps.filterDate(inicio, fim).sum().rename('chuva_t' + t);
  bandas.push(total);
  print('chuva_t' + t + ': dias na janela', chirps.filterDate(inicio, fim).size());
}
var pilha = ee.Image.cat(bandas).toFloat().clip(regiao);

var proj = chirps.first().projection().getInfo();  // grade nativa do CHIRPS (~5,5 km)
print('Projeção nativa:', proj);
Map.centerObject(regiao, 9);
Map.addLayer(pilha.select('chuva_t2025'), {min: 200, max: 900,
  palette: ['#f7fbff', '#6baed6', '#08306b']}, 'Chuva ago/2023–jul/2024 (mm)');

Export.image.toDrive({
  image: pilha,
  description: 'chirps_petrolina_juazeiro_t2017_2025',
  folder: 'mapbiomas',
  region: regiao,
  crs: proj.crs,
  crsTransform: proj.transform,
  maxPixels: 1e10
});
