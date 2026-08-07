from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.db import get_db
from app.models import Course, CourseModule, Lesson, LessonProgress, User
from app.schemas import CourseOut, CourseSummaryOut, LessonOut, ModuleOut

router = APIRouter(prefix="/api/lms", tags=["lms"], dependencies=[Depends(get_current_user)])


def _completed_lesson_ids(db: Session, user_id: int) -> set[int]:
    rows = db.query(LessonProgress.lesson_id).filter(LessonProgress.user_id == user_id).all()
    return {row[0] for row in rows}


@router.get("/courses", response_model=list[CourseSummaryOut])
def list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    courses = (
        db.query(Course)
        .filter(Course.published.is_(True))
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
        .order_by(Course.order)
        .all()
    )
    completed_ids = _completed_lesson_ids(db, user.id)

    out: list[CourseSummaryOut] = []
    for course in courses:
        lessons = [lesson for module in course.modules for lesson in module.lessons]
        out.append(
            CourseSummaryOut(
                id=course.id,
                slug=course.slug,
                title=course.title,
                description=course.description,
                order=course.order,
                lesson_count=len(lessons),
                completed_count=sum(1 for lesson in lessons if lesson.id in completed_ids),
            )
        )
    return out


@router.get("/courses/{slug}", response_model=CourseOut)
def get_course(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = (
        db.query(Course)
        .filter(Course.slug == slug, Course.published.is_(True))
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")

    completed_ids = _completed_lesson_ids(db, user.id)
    modules_out = [
        ModuleOut(
            id=module.id,
            title=module.title,
            order=module.order,
            lessons=[
                LessonOut(
                    id=lesson.id,
                    title=lesson.title,
                    description=lesson.description,
                    video_url=lesson.video_url,
                    duration_minutes=lesson.duration_minutes,
                    order=lesson.order,
                    completed=lesson.id in completed_ids,
                )
                for lesson in module.lessons
            ],
        )
        for module in course.modules
    ]
    lessons_flat = [lesson for module in modules_out for lesson in module.lessons]
    return CourseOut(
        id=course.id,
        slug=course.slug,
        title=course.title,
        description=course.description,
        order=course.order,
        lesson_count=len(lessons_flat),
        completed_count=sum(1 for lesson in lessons_flat if lesson.completed),
        modules=modules_out,
    )


@router.post("/lessons/{lesson_id}/complete", status_code=204)
def complete_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")
    existing = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if existing is None:
        db.add(LessonProgress(user_id=user.id, lesson_id=lesson_id))
        db.commit()


@router.delete("/lessons/{lesson_id}/complete", status_code=204)
def uncomplete_lesson(lesson_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(LessonProgress).filter(
        LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
    ).delete()
    db.commit()


_COURSES_SEED = [
    (
        "fundamentos",
        "Fundamentos do Trading",
        "A base para operar no mercado americano com consistência: leitura de gráfico, gestão de risco e psicologia.",
        [
            (
                "Introdução ao mercado",
                [
                    ("Como funciona a NASDAQ", "Estrutura do mercado, horários de pregão e principais índices.", 12),
                    ("Ordens, corretoras e custos", "Tipos de ordem, spread, comissões e como escolher uma corretora.", 10),
                ],
            ),
            (
                "Análise técnica essencial",
                [
                    ("Candles e price action", "Como ler candlesticks e identificar contexto de tendência.", 15),
                    ("Indicadores (RSI, MACD, médias)", "Uso prático dos indicadores já disponíveis na Ferramenta.", 18),
                ],
            ),
            (
                "Gestão de risco",
                [
                    ("Tamanho de posição e stop", "Como calcular o tamanho da posição a partir do risco por trade.", 14),
                    ("Psicologia e disciplina", "Rotina, journaling de decisões e como evitar overtrading.", 11),
                ],
            ),
        ],
    ),
    (
        "analise-tecnica-avancada",
        "Análise Técnica Avançada",
        "Leitura de contexto, estruturas de mercado e confluência de indicadores para montar setups de maior qualidade.",
        [
            (
                "Estrutura de mercado",
                [
                    ("Tendência, faixa e reversão", "Como identificar o regime de mercado antes de escolher um setup.", 16),
                    ("Suporte, resistência e zonas", "Como marcar níveis relevantes e evitar zonas subjetivas demais.", 14),
                ],
            ),
            (
                "Confluência de indicadores",
                [
                    ("Múltiplos timeframes", "Como alinhar o timeframe de decisão com o de execução.", 17),
                    ("Volume e força do movimento", "Lendo volume relativo para validar ou descartar um rompimento.", 13),
                ],
            ),
            (
                "Estudo de casos",
                [
                    ("Montando um setup na Mesa Técnica", "Passo a passo usando as ferramentas já disponíveis no OneB.", 20),
                ],
            ),
        ],
    ),
    (
        "gestao-de-risco-e-psicologia",
        "Gestão de Risco e Psicologia do Trading",
        "Como proteger o capital e manter a consistência emocional necessária para operar por muito tempo.",
        [
            (
                "Risco por operação",
                [
                    ("Definindo seu risco máximo", "Como fixar um percentual de risco por trade e por dia.", 12),
                    ("Circuit breakers pessoais", "Regras para parar de operar após uma sequência de perdas.", 10),
                ],
            ),
            (
                "Psicologia e rotina",
                [
                    ("Journaling de decisões", "Por que registrar a tese de cada trade muda o resultado no longo prazo.", 13),
                    ("Lidando com FOMO e overtrading", "Gatilhos emocionais mais comuns e como neutralizá-los na prática.", 15),
                ],
            ),
        ],
    ),
]


def seed_default_courses(db: Session) -> None:
    existing_slugs = {row[0] for row in db.query(Course.slug).all()}

    for course_order, (slug, title, description, modules_data) in enumerate(_COURSES_SEED, start=1):
        if slug in existing_slugs:
            continue
        course = Course(slug=slug, title=title, description=description, order=course_order)
        db.add(course)
        db.flush()

        for module_order, (module_title, lessons) in enumerate(modules_data, start=1):
            module = CourseModule(course_id=course.id, title=module_title, order=module_order)
            db.add(module)
            db.flush()
            for lesson_order, (lesson_title, lesson_description, duration) in enumerate(lessons, start=1):
                db.add(
                    Lesson(
                        module_id=module.id,
                        title=lesson_title,
                        description=lesson_description,
                        video_url="",
                        duration_minutes=duration,
                        order=lesson_order,
                    )
                )

    db.commit()
