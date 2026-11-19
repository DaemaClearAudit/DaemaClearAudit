import * as styles from "../../styles";
import { useInspection } from "../../hooks/useInspection";
import { InspectionStats } from "../../components/inspection/InspectionStats";
import { InspectionDetail } from "../../components/inspection/InspectionDetail";
import { Button } from "../../components/common/Button/Button";
import { Input } from "../../components/common/Input/Input";
import { Modal } from "../../components/common/Modal/Modal";
import { DashboardPage } from "../DashboardPage/DashboardPage";
import { ManagePage } from "../ManagePage/ManagePage";
import { ReviewPage } from "../ReviewPage/ReviewPage";
import { ArrowRight, CalendarDays, Plus, Sparkles, X } from "lucide-react";
import { formatDate } from "../../utils/formatDate";
import { inspectionRoutes } from "../../router";
export function InspectionPage() {
  const {
    data,
    view,
    selectedArea,
    setSelectedArea,
    filter,
    setFilter,
    selectedId,
    setSelectedId,
    search,
    setSearch,
    detailOpen,
    setDetailOpen,
    overlay,
    setOverlay,
    message,
    setMessage,
    reason,
    setReason,
    dialogOpen,
    setDialogOpen,
    sessionName,
    setSessionName,
    session,
    sessionLabel,
    tables,
    c,
    queue,
    selected,
    reviewTable,
    visible,
    updateSelected,
    changeSession,
    createSession,
    toggleSession,
    navigate,
    selectTable,
  } = useInspection();
  return (
    <>
      <header css={styles.header}>
        <div css={styles.brand}>
          <span css={styles.brandMark}>
            <Sparkles aria-hidden="true" size={19} />
          </span>
          <div>
            <b>ClassClean</b>
            <small>청소 점검 관리</small>
          </div>
        </div>
        <div css={styles.headerMeta}>
          <span css={styles.prototypeLabel}>
            <span css={styles.statusDot} /> 프로토타입 · 예시 데이터
          </span>
          <span css={styles.userAvatar}>관</span>
        </div>
      </header>
      <div css={styles.appLayout}>
        <aside css={styles.sidebar}>
          <div css={styles.workspaceLabel}>WORKSPACE</div>
          <nav>
            {inspectionRoutes.map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => navigate(id)}
                css={[styles.navItem, view === id ? styles.navItemActive : null]}
              >
                <span css={styles.navIcon}>
                  <Icon aria-hidden="true" size={17} />
                </span>{" "}
                {label}
                {id === "review" && <em>{queue.length}</em>}
              </button>
            ))}
          </nav>
          <div css={styles.sidebarNote}>
            <div css={styles.sidebarNoteIcon}>
              <Sparkles aria-hidden="true" size={20} />
            </div>
            <b>깔끔한 교실의 시작</b>
            <p>
              모든 점검 결과를
              <br />한 곳에서 확인하세요.
            </p>
          </div>
        </aside>
        <main css={styles.mainContent}>
          <div css={styles.pageHeader}>
            <div>
              <div css={styles.pageEyebrow}>INSPECTION DASHBOARD</div>
              <h1>
                {view === "dashboard" ? "전체 현황" : view === "manage" ? "판독 관리" : "검토 대기"}
              </h1>
              <p>
                {view === "dashboard"
                  ? "오늘의 청소 점검 현황을 한눈에 확인하세요."
                  : view === "manage"
                    ? "테이블별 판독 결과를 확인하고 관리하세요."
                    : "확인이 필요한 테이블을 차례대로 검토하세요."}
              </p>
            </div>
            <div css={styles.sessionControls}>
              <select
                aria-label="검사 회차 선택"
                value={session.id}
                onChange={(e) => changeSession(e.target.value)}
              >
                {data.sessions.map((s, index) => (
                  <option key={s.id} value={s.id}>
                    {index + 1}회차
                    {s.closed ? " · 종료" : ""}
                  </option>
                ))}
              </select>
              <button css={styles.primaryButton} onClick={() => setDialogOpen(true)}>
                <Plus aria-hidden="true" size={15} css={styles.smallIcon} /> 새 검사 회차
              </button>
            </div>
          </div>
          <div css={styles.sessionBanner}>
            <div>
              <span css={styles.calendarIcon}>
                <CalendarDays aria-hidden="true" size={16} />
              </span>
              <b>{sessionLabel}</b>
              <span>{formatDate(session.date)}</span>
              <span css={[styles.sessionState, session.closed ? styles.closedSessionState : null]}>
                {session.closed ? "종료됨" : "진행 중"}
              </span>
            </div>
            <button css={styles.sessionToggle} onClick={toggleSession}>
              {session.closed ? "회차 다시 열기" : "회차 종료"}{" "}
              <ArrowRight aria-hidden="true" size={13} css={styles.arrowIcon} />
            </button>
          </div>
          {message && (
            <div css={styles.statusMessage} role="status">
              {message}
              <button onClick={() => setMessage("")} aria-label="닫기">
                <X aria-hidden="true" size={20} />
              </button>
            </div>
          )}
          <InspectionStats c={c} />
          {view === "dashboard" && (
            <DashboardPage
              tables={tables}
              onOpenManage={() => navigate("manage")}
              onSelectArea={(area) => {
                setSelectedArea(area);
                setSelectedId(`${area}-04`);
                setFilter("전체");
                setReason("");
                setOverlay(false);
                setDetailOpen(true);
              }}
            />
          )}
          {view === "dashboard" && detailOpen && (
            <InspectionDetail
              table={selected}
              closed={session.closed}
              reason={reason}
              onReasonChange={setReason}
              onUpdate={updateSelected}
              overlay={overlay}
              onOverlayChange={setOverlay}
              sessionDate={session.date}
              onClose={() => setDetailOpen(false)}
              modal
            />
          )}
          {view === "manage" && (
            <ManagePage
              tables={tables}
              visibleTables={visible}
              counts={c}
              selectedArea={selectedArea}
              filter={filter}
              selectedId={selectedId}
              search={search}
              detailOpen={detailOpen}
              closed={session.closed}
              reason={reason}
              overlay={overlay}
              sessionDate={session.date}
              onAreaChange={setSelectedArea}
              onFilterChange={setFilter}
              onSelectTable={selectTable}
              onSearchChange={setSearch}
              onDetailToggle={setDetailOpen}
              onReasonChange={setReason}
              onUpdate={updateSelected}
              onOverlayChange={setOverlay}
            />
          )}
          {view === "review" && (
            <ReviewPage
              tables={tables}
              queue={queue}
              reviewTable={reviewTable}
              closed={session.closed}
              reason={reason}
              overlay={overlay}
              sessionDate={session.date}
              onSelectTable={selectTable}
              onOverlayChange={setOverlay}
              onReasonChange={setReason}
              onUpdate={updateSelected}
              onOpenManage={() => navigate("manage")}
            />
          )}{" "}
        </main>
      </div>
      <Modal
        open={dialogOpen}
        title="새 검사 회차"
        description="새로운 청소 점검을 시작합니다."
        onClose={() => setDialogOpen(false)}
      >
        <form onSubmit={createSession}>
          <label htmlFor="session-name" css={styles.formLabel}>
            회차 이름
          </label>
          <Input
            id="session-name"
            value={sessionName}
            onChange={(event) => setSessionName(event.target.value)}
            placeholder="예: 2회차"
            maxLength={40}
            required
            autoFocus
          />
          <p css={styles.formHint}>회차를 만들면 A~D 구역의 테이블 16개가 준비됩니다.</p>
          <div css={styles.modalActions}>
            <Button type="button" onClick={() => setDialogOpen(false)}>
              취소
            </Button>
            <Button variant="primary">회차 만들기</Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
