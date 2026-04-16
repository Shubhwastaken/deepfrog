import React, { useState } from "react";
import { uploadDocument } from "../services/api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const handleUpload = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const res = await uploadDocument(fd);
    alert("Job created: " + res.job_id);
  };
  return (
    <div>
      <h1>Upload Document</h1>
      <input type="file" onChange={e=>setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}
