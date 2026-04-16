import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getResults } from "../services/api";

export default function Results() {
  const { jobId } = useParams();
  const [results, setResults] = useState(null);
  useEffect(() => { getResults(jobId).then(setResults); }, [jobId]);
  if (!results) return <p>Loading...</p>;
  return <div><h1>Results</h1><pre>{JSON.stringify(results, null, 2)}</pre></div>;
}
