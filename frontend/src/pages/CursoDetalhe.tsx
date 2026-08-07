import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { VideoEmbed } from '../components/VideoEmbed';
import { useToast } from '../context/ToastContext';
import type { CourseDetail, LessonSummary } from '../types';

export function CursoDetalhe() {
  const { slug } = useParams<{ slug: string }>();
  const toast = useToast();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!slug) return;
    api
      .get<CourseDetail>(`/api/lms/courses/${slug}`)
      .then((data) => {
        setCourse(data);
        const firstIncomplete = data.modules.flatMap((m) => m.lessons).find((l) => !l.completed);
        const firstLesson = data.modules[0]?.lessons[0];
        setSelectedLessonId((firstIncomplete ?? firstLesson)?.id ?? null);
      })
      .catch(() => setError('Não foi possível carregar essa trilha.'));
  }, [slug]);

  const allLessons = useMemo(() => course?.modules.flatMap((m) => m.lessons) ?? [], [course]);
  const selectedLesson = allLessons.find((l) => l.id === selectedLessonId) ?? null;

  async function toggleComplete(lesson: LessonSummary) {
    if (!course) return;
    setSaving(true);
    try {
      if (lesson.completed) {
        await api.delete(`/api/lms/lessons/${lesson.id}/complete`);
      } else {
        await api.post(`/api/lms/lessons/${lesson.id}/complete`);
      }
      setCourse({
        ...course,
        completed_count: course.completed_count + (lesson.completed ? -1 : 1),
        modules: course.modules.map((m) => ({
          ...m,
          lessons: m.lessons.map((l) => (l.id === lesson.id ? { ...l, completed: !l.completed } : l)),
        })),
      });
    } catch {
      toast('Erro ao atualizar progresso da aula', 'error');
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <div className="container">
        <p className="form-error">{error}</p>
        <Link className="btn-link" to="/aulas">
          Voltar para Aulas
        </Link>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="container">
        <p className="muted">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Aulas</p>
          <h1>{course.title}</h1>
          <p className="muted">{course.description}</p>
        </div>
        <Link className="btn-link" to="/aulas">
          Todas as trilhas
        </Link>
      </div>

      <div className="course-shell">
        <div className="panel course-player">
          {selectedLesson ? (
            <>
              {selectedLesson.video_url ? (
                <VideoEmbed url={selectedLesson.video_url} title={selectedLesson.title} />
              ) : (
                <div className="course-video-placeholder">
                  <span>▶</span>
                  <p className="muted">Vídeo em breve · {selectedLesson.duration_minutes} min</p>
                </div>
              )}
              <h2>{selectedLesson.title}</h2>
              <p className="muted">{selectedLesson.description}</p>
              <button
                type="button"
                className={selectedLesson.completed ? 'btn-secondary' : 'auth-submit'}
                style={{ marginTop: '0.5rem' }}
                disabled={saving}
                onClick={() => toggleComplete(selectedLesson)}
              >
                {selectedLesson.completed ? 'Marcar como não concluída' : 'Marcar como concluída'}
              </button>
            </>
          ) : (
            <p className="muted">Nenhuma aula disponível ainda.</p>
          )}
        </div>

        <aside className="panel course-modules">
          <div className="panel-title">
            <h2>Conteúdo</h2>
            <span className="muted">
              {course.completed_count}/{course.lesson_count}
            </span>
          </div>
          {course.modules.map((module) => (
            <div key={module.id} className="course-module-group">
              <p className="sidebar-group-label">{module.title}</p>
              {module.lessons.map((lesson) => (
                <button
                  key={lesson.id}
                  type="button"
                  className={`course-lesson-item ${lesson.id === selectedLessonId ? 'active' : ''}`}
                  onClick={() => setSelectedLessonId(lesson.id)}
                >
                  <span className={`course-lesson-check ${lesson.completed ? 'done' : ''}`}>
                    {lesson.completed ? '✓' : ''}
                  </span>
                  <span>
                    {lesson.title}
                    <small className="muted block-text">{lesson.duration_minutes} min</small>
                  </span>
                </button>
              ))}
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
