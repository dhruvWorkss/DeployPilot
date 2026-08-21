import { ArrowPathIcon, CloudArrowUpIcon, CubeIcon, ExclamationTriangleIcon, Squares2X2Icon } from "@heroicons/react/24/outline";

const items = [
  {href:"/", label:"Overview", icon:Squares2X2Icon},
  {href:"/services", label:"Services", icon:CubeIcon},
  {href:"/deployments", label:"Deployments", icon:CloudArrowUpIcon},
  {href:"/incidents", label:"Incidents", icon:ExclamationTriangleIcon},
  {href:"/infrastructure", label:"Infrastructure", icon:ArrowPathIcon},
];

export function Sidebar({active, incidentCount=0}:{active:string; incidentCount?:number}) {
  return <aside className="sidebar">
    <a className="brand" href="/"><span className="logo">DP</span><span>DeployPilot</span></a>
    <div className="nav-label">WORKSPACE</div>
    <nav>{items.map(({href,label,icon:Icon})=><a href={href} className={active===label?"active":""} key={href}><Icon/><span>{label}</span>{label==="Incidents"&&incidentCount>0?<b>{incidentCount}</b>:null}</a>)}</nav>
    <div className="side-status"><i/><div><strong>All systems online</strong><small>Local environment</small></div></div>
    <div className="side-footer"><span className="avatar">DO</span><div><strong>DevOps Operator</strong><small>operator@deploypilot.dev</small></div><a href="/api/session/logout" title="Sign out">↗</a></div>
  </aside>;
}
