import Placeholder from '../components/Placeholder.jsx';

// 데이터는 src/api/assignments.js 의 getAssignments(date) 로 가져온다. (10/10 구현)
export default function AssignmentBoardPage() {
  return (
    <Placeholder
      title="배정 보드"
      due="10/10"
      items={[
        '날짜 선택 → getAssignments(date) 호출',
        '근로자 → 농가 배정 목록 (점수·사유 표시)',
        '미배정 근로자 / 미충족 요청 표시',
      ]}
    />
  );
}
