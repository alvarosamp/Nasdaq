import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { CourseSummary } from '../types';

export function Aulas() {
  const [courses, setCourses] = useState<CourseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CourseSummary[]>('/api/lms/courses')
      .then(setCourses)
      .catch(() => setError('Não foi possível carregar as trilhas agora.'));
  }, []);

  return (
    <div className="container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Escola</p>
          <h1>Aulas</h1>
          <p className="muted">Trilhas de curso organizadas por módulo. Continue de onde parou.</p>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      {courses === null && !error ? (
        <p className="muted">Carregando trilhas...</p>
      ) : (
        <section className="course-grid">
          {(courses ?? []).map((course) => {
            const progressPct = course.lesson_count > 0 ? Math.round((course.completed_count / course.lesson_count) * 100) : 0;
            return (
              <Link key={course.slug} to={`/aulas/${course.slug}`} className="course-card">
                <h2>{course.title}</h2>
                <p className="muted">{course.description}</p>
                <div className="course-progress">
                  <div className="course-progress-bar">
                    <div className="course-progress-fill" style={{ width: `${progressPct}%` }} />
                  </div>
                  <span className="muted">
                    {course.completed_count}/{course.lesson_count} aulas · {progressPct}%
                  </span>
                </div>
              </Link>
            );
          })}
          {courses && courses.length === 0 && <p className="muted">Nenhuma trilha publicada ainda.</p>}
        </section>
      )}
    </div>
  );
}
