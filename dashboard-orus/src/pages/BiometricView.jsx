import { useState, useEffect } from 'react';
import { Download, Loader2, Search, FileImage, FileText, CheckCircle2, UserCircle2, X, Eye } from 'lucide-react';
import { supabase } from '../supabaseClient';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const darkCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

export default function BiometricView() {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Drawer state
  const [selectedEval, setSelectedEval] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);
  
  // Image preview state
  const [previewImages, setPreviewImages] = useState([]);
  const [loadingImages, setLoadingImages] = useState(false);

  useEffect(() => {
    fetchEvaluations();
  }, []);

  const fetchEvaluations = async () => {
    try {
      const { data, error } = await supabase
        .from('evaluaciones_completas')
        .select('*')
        .order('creado_en', { ascending: false });

      if (error) throw error;
      setEvaluations(data || []);
    } catch (error) {
      console.error('Error fetching evaluations:', error);
    } finally {
      setLoading(false);
    }
  };

  const openDrawer = async (evalData) => {
    setSelectedEval(evalData);
    setAdditionalNotes('');
    setIsDrawerOpen(true);
    setPreviewImages([]);
    setLoadingImages(true);

    try {
      const folderName = evalData.wa_id;
      // Listar archivos
      const { data: files, error: listError } = await supabase.storage
        .from('biometria_test')
        .list(folderName);
        
      if (listError) throw listError;

      const imagesUrls = [];
      if (files && files.length > 0) {
        for (const file of files) {
          if (file.name === '.emptyFolderPlaceholder') continue;
          
          // Generar URL firmada temporal (válida por 1 hora = 3600s)
          const { data: urlData, error: urlError } = await supabase.storage
            .from('biometria_test')
            .createSignedUrl(`${folderName}/${file.name}`, 3600);
            
          if (urlError) {
            console.error(`Error getting URL for ${file.name}:`, urlError);
            continue;
          }
          
          imagesUrls.push({
            name: file.name,
            url: urlData.signedUrl
          });
        }
      }
      setPreviewImages(imagesUrls);
    } catch (error) {
      console.error('Error fetching images:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  const closeDrawer = () => {
    setIsDrawerOpen(false);
    setSelectedEval(null);
    setPreviewImages([]);
  };

  const handleDownloadZip = async () => {
    if (!selectedEval) return;
    setDownloadingId(selectedEval.id);

    try {
      const zip = new JSZip();
      const folderName = selectedEval.wa_id;
      
      // 1. Crear documento TXT con los datos dinámicos
      let txtContent = `DATOS BIOMÉTRICOS DEL CONSULTANTE\n`;
      txtContent += `=================================\n\n`;
      
      const excludeKeys = ['id'];
      for (const [key, value] of Object.entries(selectedEval)) {
        if (!excludeKeys.includes(key) && value !== null && value !== '') {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          const displayValue = key === 'creado_en' ? new Date(value).toLocaleString() : value;
          txtContent += `${formattedKey}: ${displayValue}\n`;
        }
      }
      
      if (additionalNotes.trim()) {
        txtContent += `\n=================================\n`;
        txtContent += `NOTAS DEL DOCTOR / DASHBOARD:\n`;
        txtContent += `=================================\n`;
        txtContent += `${additionalNotes}\n`;
      }

      zip.file("datos_paciente.txt", txtContent);

      // 2. Usar JSZipUtils o fetch normal para descargar los blobs si ya tenemos las URLs firmadas.
      // Pero por robustez, las descargamos directamente del storage:
      const { data: files, error: listError } = await supabase.storage
        .from('biometria_test')
        .list(folderName);
        
      if (!listError && files) {
        const imageFolder = zip.folder("imagenes_biometricas");
        
        for (const file of files) {
          if (file.name === '.emptyFolderPlaceholder') continue;
          
          const { data: fileData, error: downloadError } = await supabase.storage
            .from('biometria_test')
            .download(`${folderName}/${file.name}`);
            
          if (!downloadError && fileData) {
            imageFolder.file(file.name, fileData);
          }
        }
      }

      // 3. Generate and Download ZIP
      const content = await zip.generateAsync({ type: "blob" });
      saveAs(content, `Biometria_${selectedEval.nombre.replace(/\s+/g, '_')}.zip`);

    } catch (error) {
      console.error('Error creating ZIP:', error);
      alert('Hubo un error al generar el archivo ZIP. Revisa la consola.');
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredEvaluations = evaluations.filter(ev => 
    ev.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    ev.wa_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden relative">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Evaluaciones Biométricas</h1>
          <p className="text-sm text-slate-400 mt-1">
            Visualiza y descarga los datos biométricos y fotos subidas por los consultantes.
          </p>
        </div>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input 
            type="text" 
            placeholder="Buscar paciente..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-900/50 border border-zinc-700/50 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
      </div>

      <div className={`${darkCard} flex-1 flex flex-col overflow-hidden`}>
        <div className="absolute inset-0 bg-gradient-to-bl from-white/[0.02] via-transparent to-black/20 pointer-events-none" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />
        
        <div className="flex-1 overflow-auto p-2">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
              <Loader2 size={32} className="animate-spin mb-4 text-emerald-500" />
              <p>Cargando evaluaciones...</p>
            </div>
          ) : filteredEvaluations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
              <FileImage size={48} className="mb-4 opacity-30" />
              <p>No se encontraron registros biométricos.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4">
              {filteredEvaluations.map((ev) => (
                <div key={ev.id} className="bg-zinc-800/40 border border-zinc-700/50 rounded-xl p-5 hover:bg-zinc-800/80 transition-colors relative group">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0">
                      <UserCircle2 size={24} />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-slate-200 font-semibold truncate" title={ev.nombre}>{ev.nombre}</h3>
                      <p className="text-xs text-slate-400 truncate">{ev.wa_id}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-6">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Ciudad:</span>
                      <span className="text-slate-300 truncate ml-2">{ev.ciudad || '-'}</span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Edad:</span>
                      <span className="text-slate-300">{ev.edad ? `${ev.edad} años` : '-'}</span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Fecha:</span>
                      <span className="text-slate-300">{new Date(ev.creado_en).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => openDrawer(ev)}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition-all text-sm font-medium"
                  >
                    <Eye size={16} /> Ver Detalles y Fotos
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Drawer Panel */}
      <div 
        className={`fixed inset-y-0 right-0 w-full max-w-4xl bg-zinc-950 border-l border-zinc-800 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {selectedEval && (
          <>
            <div className="h-16 px-6 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50 shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                  <UserCircle2 size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-100 leading-tight">{selectedEval.nombre}</h2>
                  <p className="text-xs text-emerald-400">{selectedEval.wa_id}</p>
                </div>
              </div>
              <button 
                onClick={closeDrawer}
                className="p-2 text-slate-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-auto p-6 flex flex-col md:flex-row gap-6">
              {/* Columna Izquierda: Datos y Notas */}
              <div className="flex-1 flex flex-col gap-6">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4 border-b border-zinc-800 pb-2">Resumen de Datos</h3>
                  <div className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
                    <div>
                      <span className="block text-xs text-slate-500">Edad</span>
                      <span className="text-slate-300">{selectedEval.edad || '-'}</span>
                    </div>
                    <div>
                      <span className="block text-xs text-slate-500">Ciudad</span>
                      <span className="text-slate-300">{selectedEval.ciudad || '-'}</span>
                    </div>
                    <div>
                      <span className="block text-xs text-slate-500">Ocupación</span>
                      <span className="text-slate-300">{selectedEval.ocupacion || '-'}</span>
                    </div>
                    <div>
                      <span className="block text-xs text-slate-500">Motivo de consulta</span>
                      <span className="text-slate-300">{selectedEval.motivo_consulta || '-'}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex-1 flex flex-col">
                  <label className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                    <FileText size={16} />
                    Notas del Doctor (Opcional)
                  </label>
                  <textarea
                    value={additionalNotes}
                    onChange={(e) => setAdditionalNotes(e.target.value)}
                    placeholder="Escribe aquí observaciones. Se guardarán en el archivo datos_paciente.txt al exportar el ZIP."
                    className="flex-1 w-full min-h-[120px] bg-zinc-950 border border-zinc-700 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 resize-none"
                  />
                </div>
              </div>

              {/* Columna Derecha: Fotos */}
              <div className="flex-[1.5] bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col">
                <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2 border-b border-zinc-800 pb-2">
                  <FileImage size={16} />
                  Galería Biométrica
                </h3>
                
                <div className="flex-1 overflow-y-auto pr-2">
                  {loadingImages ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                      <Loader2 size={32} className="animate-spin mb-4 text-emerald-500" />
                      <p className="text-sm">Cargando imágenes de Supabase...</p>
                    </div>
                  ) : previewImages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                      <FileImage size={40} className="mb-3 opacity-30" />
                      <p className="text-sm">No hay imágenes en el bucket para este paciente.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {previewImages.map((img, idx) => (
                        <div key={idx} className="group relative aspect-[3/4] bg-zinc-950 rounded-lg overflow-hidden border border-zinc-800">
                          <img 
                            src={img.url} 
                            alt={img.name} 
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                            <span className="text-xs text-slate-300 truncate w-full">{img.name}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="h-20 px-6 border-t border-zinc-800 bg-zinc-900/50 shrink-0 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <CheckCircle2 size={16} className="text-emerald-500" />
                <span>Revisa las imágenes antes de exportar.</span>
              </div>
              <button
                onClick={handleDownloadZip}
                disabled={downloadingId === selectedEval.id}
                className="px-6 py-2.5 rounded-lg text-sm font-medium bg-emerald-500 hover:bg-emerald-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {downloadingId === selectedEval.id ? (
                  <><Loader2 size={16} className="animate-spin" /> Empaquetando...</>
                ) : (
                  <><Download size={16} /> Exportar Paquete ZIP</>
                )}
              </button>
            </div>
          </>
        )}
      </div>

      {/* Backdrop for Drawer */}
      {isDrawerOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
          onClick={closeDrawer}
        />
      )}
    </div>
  );
}
