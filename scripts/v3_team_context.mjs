// Reuse the pinned historical source's own aggregation; no new EPA/RZ definitions.
import fs from 'node:fs';
import zlib from 'node:zlib';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [upstream,pbp,season,output]=process.argv.slice(2);
const {aggregateTeamContext}=await import(pathToFileURL(path.resolve(upstream,'lib/nflverse.mjs')));
const derived=aggregateTeamContext(zlib.gunzipSync(fs.readFileSync(pbp)).toString('utf8'),{season:Number(season)});
fs.writeFileSync(output,JSON.stringify({schemaVersion:1,season:Number(season),...derived}));
