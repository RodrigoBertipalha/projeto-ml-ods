// Exporta o MapBiomas Coleção 10 (cobertura e uso, 30 m) recortado para o
// retângulo de Petrolina-PE/Juazeiro-BA, 2015–2024, uma banda por ano.
// Rodar no Code Editor do Google Earth Engine (code.earthengine.google.com);
// o GeoTIFF vai para a pasta "mapbiomas" do Google Drive e deve ser copiado
// manualmente para data/raw/mapbiomas/ (ver docs/fontes-de-dados.md).

var regiao = ee.Geometry.Rectangle([-40.97, -10.0, -39.84, -8.61]);
var col = ee.ImageCollection('projects/mapbiomas-public/assets/brazil/lulc/v1')
  .filter(ee.Filter.eq('collection_id', 10.0))
  .filter(ee.Filter.eq('version', 'v1'));
print('Imagens por ano (conferir 2015–2024):', col.aggregate_histogram('year'));

var bandas = [];
for (var ano = 2015; ano <= 2024; ano++) {
  bandas.push(col.filter(ee.Filter.eq('year', ano)).mosaic().rename('classification_' + ano));
}
var pilha = ee.Image.cat(bandas).toByte().clip(regiao);

var proj = col.first().projection().getInfo();  // grade nativa do MapBiomas (~30 m)
print('Projeção nativa:', proj);
Map.centerObject(regiao, 9);
Map.addLayer(pilha.select('classification_2024'), {min: 0, max: 75}, 'MapBiomas 2024');

Export.image.toDrive({
  image: pilha,
  description: 'mapbiomas_c10_petrolina_juazeiro_2015_2024',
  folder: 'mapbiomas',
  region: regiao,
  crs: proj.crs,
  crsTransform: proj.transform,
  maxPixels: 1e10
});
