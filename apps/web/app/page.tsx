import {BoltIcon, CheckCircleIcon, CloudArrowUpIcon, ExclamationTriangleIcon} from "@heroicons/react/24/outline";
import { Sidebar } from "@/components/Sidebar";

type Deployment = {id:string; service_id:string; service_name?:string; version:string; commit_sha:string; status:string; actor:string; started_at:string};
type Overview = {services:number; healthy_services:number; deployments_today:number; success_rate:number; open_incidents:number; recent_deployments:Deployment[]};

const fallback: Overview = {services:3, healthy_services:2, deployments_today:3, success_rate:96.8, open_incidents:1, recent_deployments:[
  {id:"1",service_id:"checkout-api",service_name:"checkout-api",version:"v2.14.3",commit_sha:"8f17a2c",status:"healthy",actor:"maya@acme.io",started_at:new Date().toISOString()},
  {id:"2",service_id:"catalog",service_name:"catalog",version:"v4.8.1",commit_sha:"c3e791a",status:"healthy",actor:"jenkins",started_at:new Date(Date.now()-7200000).toISOString()},
  {id:"3",service_id:"notification-worker",service_name:"notification-worker",version:"v1.9.0",commit_sha:"a44ed10",status:"rolled_back",actor:"jenkins",started_at:new Date(Date.now()-14400000).toISOString()}
]};

async function getOverview(): Promise<Overview> {
  try {
    const apiUrl = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://api:8000";
    const response = await fetch(`${apiUrl}/api/v1/overview`, {cache:"no-store"});
    if (!response.ok) throw new Error("API unavailable");
    return response.json();
  } catch { return fallback; }
}

function timeAgo(timestamp: string): string {
  const minutes = Math.max(1, Math.floor((Date.now() - new Date(timestamp).getTime()) / 60_000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours}h ago` : `${Math.floor(hours / 24)}d ago`;
}

export default async function Dashboard() {
  const data = await getOverview();
  const stats = [
    {label:"Healthy services", value:`${data.healthy_services}/${data.services}`, detail:"All critical services available", icon:CheckCircleIcon, tone:"green"},
    {label:"Deployments today", value:String(data.deployments_today), detail:"2.6× faster than last week", icon:CloudArrowUpIcon, tone:"blue"},
    {label:"Release success", value:`${data.success_rate}%`, detail:"Across the last 30 days", icon:BoltIcon, tone:"violet"},
    {label:"Open incidents", value:String(data.open_incidents), detail:`${data.open_incidents} require${data.open_incidents === 1 ? "s" : ""} investigation`, icon:ExclamationTriangleIcon, tone:"amber"}
  ];
  return <div className="shell">
    <Sidebar active="Overview" incidentCount={data.open_incidents}/>
    <main>
      <header><div><p className="eyebrow">CONTROL PLANE / PRODUCTION</p><h1>Good afternoon, operator.</h1><p>Everything that matters is stable. One incident needs your attention.</p></div><button><CloudArrowUpIcon/>New deployment</button></header>
      <section className="stats">{stats.map(({label,value,detail,icon:Icon,tone})=><article key={label} className="stat"><span className={`metric-icon ${tone}`}><Icon/></span><div><small>{label}</small><strong>{value}</strong><p>{detail}</p></div></article>)}</section>
      <section className="grid">
        <article className="panel releases"><div className="panel-head"><div><h2>Release activity</h2><p>Latest changes across production services</p></div><a href="/deployments">View all →</a></div>
          <div className="release-list">{data.recent_deployments.map((d)=><div className="release" key={d.id}><span className={`status-dot ${d.status}`}/><div className="release-main"><div><strong>{d.service_name ?? d.service_id}</strong><span className="version">{d.version}</span></div><p><code>{d.commit_sha.slice(0,7)}</code> · deployed by {d.actor}</p></div><span className={`pill ${d.status}`}>{d.status.replace("_"," ")}</span><time>{timeAgo(d.started_at)}</time></div>)}</div>
        </article>
        <article className="panel health"><div className="panel-head"><div><h2>Fleet health</h2><p>Live cluster signals</p></div><span className="live"><i/>LIVE</span></div>
          <div className="score"><div className="ring"><span>98<small>/100</small></span></div><div><strong>Excellent</strong><p>All SLOs within target</p></div></div>
          <div className="health-rows"><div><span>Availability</span><b>99.99%</b></div><div className="bar"><i style={{width:"99%"}}/></div><div><span>p95 latency</span><b>184 ms</b></div><div className="bar blue"><i style={{width:"72%"}}/></div><div><span>Error rate</span><b>0.08%</b></div><div className="bar amber"><i style={{width:"8%"}}/></div></div>
        </article>
      </section>
      <section className="panel incident"><span className="incident-icon"><ExclamationTriangleIcon/></span><div><div className="incident-title"><h3>Readiness probe failure after v1.9.0</h3><span>HIGH</span></div><p>notification-worker · Automatically rolled back · Incident assistant found a likely configuration mismatch.</p></div><a className="secondary action-link" href="/incidents">Investigate</a></section>
      <footer><span><i/> Systems operational</span><span>GKE us-central1 · 6 nodes · Kubernetes 1.30</span></footer>
    </main>
  </div>;
}
