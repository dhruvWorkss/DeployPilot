import { Sidebar } from "./Sidebar";

export function PageShell({active,title,description,children,incidentCount=0}:{active:string;title:string;description:string;children:React.ReactNode;incidentCount?:number}) {
  return <div className="shell"><Sidebar active={active} incidentCount={incidentCount}/><main><header className="page-header"><div><p className="eyebrow">CONTROL PLANE / PRODUCTION</p><h1>{title}</h1><p>{description}</p></div></header>{children}<footer><span><i/> Systems operational</span><span>DeployPilot local control plane</span></footer></main></div>;
}
