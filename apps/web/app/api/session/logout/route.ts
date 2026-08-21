import { NextRequest, NextResponse } from "next/server";
export function GET(_request:NextRequest){const response=new NextResponse(null,{status:303,headers:{Location:"/login"}});response.cookies.delete("deploypilot_session");return response;}
