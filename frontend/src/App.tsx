import type { ReactNode } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import { ConfirmProvider } from './components/ConfirmModal';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Cadastro } from './pages/Cadastro';
import { Landing } from './pages/Landing';
import { Estrategias } from './pages/Estrategias';
import { Comunidade } from './pages/Comunidade';
import { Planos } from './pages/Planos';
import { Sobre } from './pages/Sobre';
import { Aplicacoes } from './pages/Aplicacoes';
import { Hub } from './pages/Hub';
import { Aulas } from './pages/Aulas';
import { Aprendizado } from './pages/Aprendizado';
import { CursoDetalhe } from './pages/CursoDetalhe';
import { Lives } from './pages/Lives';
import { Dashboard } from './pages/Dashboard';
import { Watchlist } from './pages/Watchlist';
import { Mercado } from './pages/Mercado';
import { AnaliseMatinal } from './pages/AnaliseMatinal';
import { Alertas } from './pages/Alertas';
import { Posicoes } from './pages/Posicoes';
import { Assistente } from './pages/Assistente';
import { Usuarios } from './pages/Usuarios';
import { AtivoDetalhe } from './pages/AtivoDetalhe';
import { ComoUsar } from './pages/ComoUsar';
import { Copiloto } from './pages/Copiloto';
import { Perfil } from './pages/Perfil';
import { Saas } from './pages/Saas';
import { Inteligencia } from './pages/Inteligencia';
import { Operacoes } from './pages/Operacoes';
import { MesaTecnica } from './pages/MesaTecnica';
import { MesaIA } from './pages/MesaIA';
import { Regime } from './pages/Regime';
import { ResumoDiario } from './pages/ResumoDiario';

function Layout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="academy-layout">{children}</main>
      <footer className="disclaimer app-disclaimer">
        Ferramenta apenas de monitoramento e sugestão. Não executa ordens e não constitui
        recomendação de investimento. Dados podem ter atraso. Valide qualquer sinal antes de
        decidir.
      </footer>
    </>
  );
}

function ToolLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <div className="app-shell">
        <Sidebar />
        <main className="app-shell-content terminal-layout">{children}</main>
      </div>
      <footer className="disclaimer app-disclaimer terminal-disclaimer">
        Ferramenta apenas de monitoramento e sugestão. Não executa ordens e não constitui
        recomendação de investimento. Dados podem ter atraso. Valide qualquer sinal antes de
        decidir.
      </footer>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <ConfirmProvider>
              <Routes>
                <Route
                  path="/"
                  element={<Landing />}
                />
                <Route path="/aulas" element={<Aulas />} />
                <Route path="/aplicacoes" element={<Aplicacoes />} />
                <Route path="/estrategias" element={<Estrategias />} />
                <Route path="/comunidade" element={<Comunidade />} />
                <Route path="/planos" element={<Planos />} />
                <Route path="/sobre" element={<Sobre />} />
                <Route path="/login" element={<Login />} />
                <Route path="/cadastro" element={<Cadastro />} />

                <Route element={<ProtectedRoute />}>
                  <Route
                    path="/inicio"
                    element={
                      <Layout>
                        <Hub />
                      </Layout>
                    }
                  />
                  <Route
                    path="/aprendizado"
                    element={
                      <Layout>
                        <Aprendizado />
                      </Layout>
                    }
                  />
                  <Route
                    path="/aulas/:slug"
                    element={
                      <Layout>
                        <CursoDetalhe />
                      </Layout>
                    }
                  />
                  <Route
                    path="/lives"
                    element={
                      <Layout>
                        <Lives />
                      </Layout>
                    }
                  />
                  <Route
                    path="/perfil"
                    element={
                      <Layout>
                        <Perfil />
                      </Layout>
                    }
                  />

                  <Route
                    path="/ferramenta"
                    element={
                      <ToolLayout>
                        <Dashboard />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/watchlist"
                    element={
                      <ToolLayout>
                        <Watchlist />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/mercado"
                    element={
                      <ToolLayout>
                        <Mercado />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/analise-matinal"
                    element={
                      <ToolLayout>
                        <AnaliseMatinal />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/alertas"
                    element={
                      <ToolLayout>
                        <Alertas />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/posicoes"
                    element={
                      <ToolLayout>
                        <Posicoes />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/assistente"
                    element={
                      <ToolLayout>
                        <Assistente />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/copiloto"
                    element={
                      <ToolLayout>
                        <Copiloto />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/saas"
                    element={
                      <ToolLayout>
                        <Saas />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/inteligencia"
                    element={
                      <ToolLayout>
                        <Inteligencia />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/operacoes"
                    element={
                      <ToolLayout>
                        <Operacoes />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/resumo-diario"
                    element={
                      <ToolLayout>
                        <ResumoDiario />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/mesa-ia"
                    element={
                      <ToolLayout>
                        <MesaIA />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/mesa-tecnica"
                    element={
                      <ToolLayout>
                        <MesaTecnica />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/regime"
                    element={
                      <ToolLayout>
                        <Regime />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/ativo/:symbol"
                    element={
                      <ToolLayout>
                        <AtivoDetalhe />
                      </ToolLayout>
                    }
                  />
                  <Route
                    path="/como-usar"
                    element={
                      <ToolLayout>
                        <ComoUsar />
                      </ToolLayout>
                    }
                  />

                  <Route element={<AdminRoute />}>
                    <Route
                      path="/usuarios"
                      element={
                        <ToolLayout>
                          <Usuarios />
                        </ToolLayout>
                      }
                    />
                  </Route>
                </Route>
              </Routes>
            </ConfirmProvider>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
