// Compass Playground script for a minimal demo database.
// Database name: Demo_Grietas
// If you want thumbnails in the app, copy matching image files to ./imagenes/ with the same names used below.

const demoDb = db.getSiblingDB("Demo_Grietas");

demoDb.Clases.deleteMany({});
demoDb.Fuente.deleteMany({});
demoDb.Formato.deleteMany({});
demoDb.Campos.deleteMany({});
demoDb.Docs.deleteMany({});

demoDb.Campos.insertMany([
  {
    _id: 0,
    nombre: "fuente",
    cod: 4,
    campos_etiqueta: { fuente: "str" },
    coleccion: "Fuente"
  },
  {
    _id: 1,
    nombre: "formato",
    cod: 4,
    campos_etiqueta: { formato: "str" },
    coleccion: "Formato"
  },
  {
    _id: 2,
    nombre: "clase",
    cod: 0,
    campos_etiqueta: { nombre: "str", clase: "str" },
    coleccion: "Clases"
  }
]);

demoDb.Clases.insertMany([
  {
    _id: 0,
    nombre: "Inofensiva",
    clase: "Inofensiva"
  },
  {
    _id: 1,
    nombre: "Neutra",
    clase: "Neutra"
  },
  {
    _id: 2,
    nombre: "Peligrosa",
    clase: "Peligrosa"
  }
]);

demoDb.Fuente.insertOne({
  _id: 0,
  fuente: "DemoGrietas",
  nombre: "DemoGrietas"
});

demoDb.Formato.insertOne({
  _id: 0,
  formato: "Color",
  nombre: "Color"
});

demoDb.Docs.insertMany([
  {
    _id: 0,
    imagen_rgb: "http://localhost:5001/imagen_base64/demo_grietas_inofensiva_1.jpg",
    validada: true,
    usuario: "demo",
    clase: 0,
    fuente: 0,
    formato: 0
  },
  {
    _id: 1,
    imagen_rgb: "http://localhost:5001/imagen_base64/demo_grietas_neutra_1.jpg",
    validada: true,
    usuario: "demo",
    clase: 1,
    fuente: 0,
    formato: 0
  },
  {
    _id: 2,
    imagen_rgb: "http://localhost:5001/imagen_base64/demo_grietas_peligrosa_1.jpg",
    validada: true,
    usuario: "demo",
    clase: 2,
    fuente: 0,
    formato: 0
  }
]);

print("Demo_Grietas creada con Clases, Fuente, Formato y Docs.");
