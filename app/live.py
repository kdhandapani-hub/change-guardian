import argparse,asyncio,json,uuid
from dotenv import load_dotenv
from app.core import ROOT
from app.jenkins import session
from app.investigate import run_investigation

async def main():
    load_dotenv(ROOT/".env",override=False)
    p=argparse.ArgumentParser();p.add_argument("--build",required=True,type=int);p.add_argument("--context",default=str(ROOT/"fixtures/analyser-context.json"));a=p.parse_args()
    context=json.loads(__import__("pathlib").Path(a.context).read_text())
    async with session() as client:
        result=await run_investigation(client,a.build,context,str(uuid.uuid4()))
    out=ROOT/"runtime/investigations";out.mkdir(parents=True,exist_ok=True)
    (out/f"build-{a.build}.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__":asyncio.run(main())
