import { useState, useEffect } from 'react';
import { Download, Loader2, Search, FileImage, FileText, CheckCircle2, UserCircle2 } from 'lucide-react';
import { supabase } from '../supabaseClient';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const darkCard = "relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-black border border-zinc-700/50 shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-md";

export default function BiometricView() {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEval, setSelectedEval] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

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

  const openDownloadModal = (evalData) => {
    setSelectedEval(evalData);
    setAdditionalNotes('');
    setIsModalOpen(true);
  };

  const handleDownloadZip = async () => {
    if (!selectedEval) return;
    setDownloadingId(selectedEval.id);
    setIsModalOpen(false);

    try {
      const zip = new JSZip();
      const folderName = selectedEval.wa_id;
      
      // 1. Crear documento TXT con los datos dinámicos
      let txtContent = `DATOS BIOMÉTRICOS DEL CONSULTANTE\n`;
      txtContent += `=================================\n\n`;
      
      const excludeKeys = ['id']; // keys a ignorar en el txt
      for (const [key, value] of Object.entries(selectedEval)) {
        if (!excludeKeys.includes(key) && value !== null && value !== '') {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          // Formateo especial para fechas
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

      // 2. Fetch images from Supabase Storage
      const { data: files, error: listError } = await supabase.storage
        .from('biometria_test')
        .list(folderName);
        
      if (listError) {
        console.error('Error listing files in storage:', listError);
      }

      if (files && files.length > 0) {
        const imageFolder = zip.folder("imagenes_biometricas");
        
        for (const file of files) {
          if (file.name === '.emptyFolderPlaceholder') continue;
          
          const { data: fileData, error: downloadError } = await supabase.storage
            .from('biometria_test')
            .download(`${folderName}/${file.name}`);
            
          if (downloadError) {
            console.error(`Error downloading ${file.name}:`, downloadError);
            continue;
          }
          
          imageFolder.file(file.name, fileData);
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
    <div className="flex-1 flex flex-col p-6 overflow-auto">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Evaluaciones Biométricas</h1>
          <p className="text-sm text-slate-400 mt-1">
            Visualiza y descarga los datos biométricos y fotos subidas por los consultantes en un solo paquete ZIP.
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

      <div className={`${darkCard} flex-1 flex flex-col`}>
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
                <div key={ev.id} className="bg-zinc-800/40 border border-zinc-700/50 rounded-xl p-5 hover:bg-zinc-800/60 transition-colors relative group">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0">
                      <UserCircle2 size={24} />
                    </div>
                    <div>
                      <h3 className="text-slate-200 font-semibold truncate" title={ev.nombre}>{ev.nombre}</h3>
                      <p className="text-xs text-slate-400 truncate">{ev.wa_id}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-6">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Ciudad:</span>
                      <span className="text-slate-300">{ev.ciudad || '-'}</span>
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
                    onClick={() => openDownloadModal(ev)}
                    disabled={downloadingId === ev.id}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition-all text-sm font-medium disabled:opacity-50"
                  >
                    {downloadingId === ev.id ? (
                      <><Loader2 size={16} className="animate-spin" /> Procesando ZIP...</>
                    ) : (
                      <><Download size={16} /> Exportar Paquete ZIP</>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal para Notas Adicionales */}
      {isModalOpen && selectedEval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-zinc-900 border border-zinc-700 shadow-2xl rounded-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-6">
              <h2 className="text-xl font-bold text-slate-100 mb-2">Preparar Paquete Biométrico</h2>
              <p className="text-sm text-slate-400 mb-6">
                Paciente: <span className="text-emerald-400 font-medium">{selectedEval.nombre}</span>
              </p>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                  <FileText size={16} />
                  Añadir notas del Doctor (Opcional)
                </label>
                <textarea
                  value={additionalNotes}
                  onChange={(e) => setAdditionalNotes(e.target.value)}
                  placeholder="Escribe aquí notas adicionales, observaciones, etc. Esto se incluirá en el documento datos_paciente.txt dentro del ZIP."
                  className="w-full h-32 bg-zinc-950 border border-zinc-700 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 resize-none"
                />
              </div>

              <div className="flex items-center gap-3 bg-zinc-800/50 p-3 rounded-lg border border-zinc-700/50 mb-6 text-sm text-slate-300">
                <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />
                <p>El ZIP incluirá el TXT con todos los datos del paciente (formulario), tus notas, y las imágenes de Supabase.</p>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-zinc-800 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleDownloadZip}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-500 hover:bg-emerald-600 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all flex items-center gap-2"
                >
                  <Download size={16} />
                  Generar y Descargar ZIP
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
