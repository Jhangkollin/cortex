import type { DiscoverData } from "@/lib/discover/types";

export function QuestionTop10({ questions }: { questions: DiscoverData["questions"] }) {
  return (
    <div className="card q10">
      <div className="q10-hd">
        <div>
          <h3>相關問題 Top 10 <small>(讀者正在問)</small></h3>
          <div className="q10-sub">真實問題・真實月度瀏覽・你的品牌可以成為答案的一部分</div>
        </div>
        <span className="q10-badge">SAMPLE · TOP 500</span>
      </div>
      <div className="q10-cols">
        <div>QUESTION</div>
        <div>VIEWS</div>
        <div>PUBLISHER</div>
        <div>PRODUCT MATCH</div>
      </div>
      {questions.map((q, i) => (
        <div className="q10-row" key={i}>
          <div className="q10-q">{q.q}</div>
          <div className="q10-v">{q.views.toLocaleString()}</div>
          <div className="q10-pub">{q.publisher}</div>
          <div className="q10-match">
            {q.match.split("／").map((m, j) => (
              <span className="q10-match-pill" key={j}>{m}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
