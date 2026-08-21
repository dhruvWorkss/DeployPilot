import { NextRequest, NextResponse } from "next/server";

export async function POST(request:NextRequest){
  const form=await request.formData();
  const email=String(form.get("email")??"");
  const password=String(form.get("password")??"");
  const expectedEmail=process.env.DEPLOYPILOT_DEMO_EMAIL??"operator@deploypilot.dev";
  const expectedPassword=process.env.DEPLOYPILOT_DEMO_PASSWORD??"DeployPilot2026!";
  if(email!==expectedEmail||password!==expectedPassword) return new NextResponse(null,{status:303,headers:{Location:"/login?error=1"}});
  const response=new NextResponse(null,{status:303,headers:{Location:"/"}});
  response.cookies.set("deploypilot_session","local-operator",{httpOnly:true,sameSite:"lax",secure:process.env.NODE_ENV==="production"&&request.nextUrl.protocol==="https:",maxAge:60*60*8,path:"/"});
  return response;
}
