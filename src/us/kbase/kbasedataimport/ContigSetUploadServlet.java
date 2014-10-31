package us.kbase.kbasedataimport;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.fileupload.FileItem;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.servlet.ServletContextHandler;
import org.eclipse.jetty.servlet.ServletHolder;
import us.kbase.auth.AuthToken;
import us.kbase.common.service.UObject;
import us.kbase.common.utils.FastaReader;
import us.kbase.genbank.GbkUploader;
import us.kbase.genbank.ObjectStorage;
import us.kbase.kbasegenomes.Contig;
import us.kbase.kbasegenomes.ContigSet;
import us.kbase.kbasegenomes.Genome;
import us.kbase.workspace.ObjectSaveData;
import us.kbase.workspace.SaveObjectsParams;
import us.kbase.workspace.WorkspaceClient;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.*;
import java.net.URL;
import java.util.*;
import java.util.zip.GZIPInputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class ContigSetUploadServlet extends HttpServlet {
    private static final long serialVersionUID = -1L;

    private static File tempDir = null;
    private static String wsUrl = null;

    private static File getTempDir() throws IOException {
        if (tempDir == null)
            tempDir = KBaseDataImportServer.getTempDir();
        return tempDir;
    }

    private static String getWsUrl() throws IOException {
        if (wsUrl == null)
            wsUrl = KBaseDataImportServer.getWorkspaceServiceURL();
        return wsUrl;
    }

    @Override
    protected void doOptions(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        setupResponseHeaders(request, response);
        response.setContentLength(0);
        response.getOutputStream().print("");
        response.getOutputStream().flush();
    }

    private static void setupResponseHeaders(HttpServletRequest request,
                                             HttpServletResponse response) {
        response.setHeader("Access-Control-Allow-Origin", "*");
        String allowedHeaders = request.getHeader("HTTP_ACCESS_CONTROL_REQUEST_HEADERS");
        response.setHeader("Access-Control-Allow-Headers", allowedHeaders == null ? "authorization" : allowedHeaders);
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        int maxMemoryFileSize = 50 * 1024 * 1024;
        File dir = getTempDir();
        DiskFileItemFactory factory = new DiskFileItemFactory(maxMemoryFileSize, dir);
        ServletFileUpload upload = new ServletFileUpload(factory);
        FileItem file = null;
        List<File> tempFiles = new ArrayList<File>();
        try {
            String token = null;
            String ws = null;
            String id = null;
            String type = null;
            List<?> items = upload.parseRequest(request);
            Iterator<?> it = items.iterator();
            while (it.hasNext()) {
                FileItem item = (FileItem) it.next();
                if (item.isFormField()) {
                    if (item.getFieldName().equals("token")) {
                        token = item.getString();
                    } else if (item.getFieldName().equals("ws")) {
                        ws = item.getString();
                    } else if (item.getFieldName().equals("id")) {
                        id = item.getString();
                    } else if (item.getFieldName().equals("type")) {
                        type = item.getString();
                    } else {
                        throw new ServletException("Unknown parameter: " + item.getFieldName());
                    }
                } else if (item.getFieldName().equals("file")) {
                    long size = item.getSize();
                    file = item;
                    if (size > maxMemoryFileSize) {
                        throw new ServletException("File size is too large: " + size + " > " + maxMemoryFileSize);
                    }
                } else {
                    throw new ServletException("Unknown parameter: " + item.getFieldName());
                }
            }
            check(token, "token");
            check(ws, "ws");
            check(id, "id");
            check(type, "type");
            check(file, "file");
            if (type.equals("contigfasta")) {
                FastaReader fr = new FastaReader(new InputStreamReader(file.getInputStream()));
                Map<String, String> contigIdToSeq = fr.readAll();
                fr.close();
                if (contigIdToSeq.size() == 0)
                    throw new ServletException("Data was not defined or empty");
                List<Contig> contigList = new ArrayList<Contig>();
                for (String contigId : contigIdToSeq.keySet()) {
                    String seq = contigIdToSeq.get(contigId);
                    contigList.add(new Contig().withId(contigId).withName(contigId).withSequence(seq)
                            .withLength((long) seq.length()).withMd5("md5"));
                }
                ContigSet contigSet = new ContigSet().withContigs(contigList).withId(id).withMd5("md5").withName(id)
                        .withSource("User uploaded data").withSourceId("USER").withType("Organism");
                WorkspaceClient wc = createWsClient(token);
                ObjectSaveData data = new ObjectSaveData().withName(id).withType("KBaseGenomes.ContigSet").withData(new UObject(contigSet));
                try {
                    data.withObjid(Long.parseLong(id));
                } catch (NumberFormatException ex) {
                    data.withName(id);
                }
                wc.saveObjects(new SaveObjectsParams().withWorkspace(ws).withObjects(Arrays.asList(data)));
                response.getOutputStream().write("Contig Set was successfuly uploaded".getBytes());
            } else if (type.equals("genomegbk")) {
                String wsUrl = getWsUrl();
                if (file.getName().endsWith(".zip")) {
                    ZipInputStream zis = new ZipInputStream(file.getInputStream());
                    while (true) {
                        ZipEntry ze = zis.getNextEntry();
                        if (ze == null)
                            break;
                        File tempFile = File.createTempFile(id, ".gbk", dir);
                        tempFiles.add(tempFile);
                        OutputStream os = new FileOutputStream(tempFile);
                        copy(zis, os);
                        os.close();
                        zis.closeEntry();
                    }
                    zis.close();
                    ArrayList vars = (ArrayList) GbkUploader.uploadGbk(tempFiles, wsUrl, ws, id, token);
                    GbkUploader.uploadtoWS((ObjectStorage)vars.get(0), ws, id, token, (Genome)vars.get(4), (String) vars.get(5), (ContigSet) vars.get(6), (Map<String, String>)vars.get(7));
                    //GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);

                } else if (file.getName().endsWith(".tar.gz") || file.getName().endsWith(".tgz")) {
                    throw new ServletException("Tar files are not supported, please use zip instead.");
                } else if (file.getName().endsWith(".gz")) {
                    File tempFile = File.createTempFile(id, ".gbk", dir);
                    tempFiles.add(tempFile);
                    GZIPInputStream is = new GZIPInputStream(file.getInputStream());
                    OutputStream os = new FileOutputStream(tempFile);
                    copy(is, os);
                    os.close();
                    is.close();
                    ArrayList vars = (ArrayList) GbkUploader.uploadGbk(Arrays.asList(tempFile), wsUrl, ws, id, token);
                    GbkUploader.uploadtoWS((ObjectStorage)vars.get(0), ws, id, token, (Genome)vars.get(4), (String) vars.get(5), (ContigSet) vars.get(6), (Map<String, String>)vars.get(7));
                    //GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);

                } else {
                    File tempFile = File.createTempFile(id, ".gbk", dir);
                    tempFiles.add(tempFile);
                    file.write(tempFile);
                    ArrayList vars = (ArrayList) GbkUploader.uploadGbk(Arrays.asList(tempFile), wsUrl, ws, id, token);
                    GbkUploader.uploadtoWS((ObjectStorage)vars.get(0), ws, id, token, (Genome)vars.get(4), (String) vars.get(5), (ContigSet) vars.get(6), (Map<String, String>)vars.get(7));
                    //GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);

                }
                setupResponseHeaders(request, response);
                response.getOutputStream().write("Genome was successfuly uploaded".getBytes());
            } else {
                throw new ServletException("Unknown file type: " + type);
            }
        } catch (Throwable ex) {
            setupResponseHeaders(request, response);
            ex.printStackTrace(new PrintStream(response.getOutputStream()));
        } finally {
            if (file != null)
                file.delete();
            for (File f : tempFiles)
                if (f.exists())
                    f.delete();
        }
    }

    private static void check(Object obj, String param) throws ServletException {
        if (obj == null)
            throw new ServletException("Parameter " + param + " wasn't defined");
    }

    private static Map<String, List<String>> loadGenomeToPaths() throws Exception {
        InputStream is = ContigSetUploadServlet.class.getResourceAsStream("genome2ftp.properties");
        return new ObjectMapper().readValue(is, new TypeReference<Map<String, List<String>>>() {
        });
    }

    public static List<String> getNcbiGenomeNames() throws Exception {
        return new ArrayList<String>(loadGenomeToPaths().keySet());
    }

    public static void importNcbiGenome(String genomeName, String ws, String id, String token) throws Exception {
        List<String> paths = loadGenomeToPaths().get(genomeName);
        if (paths == null)
            throw new IllegalStateException("NCBI genome name is not found: " + genomeName);
        File dir = getTempDir();
        List<File> files = new ArrayList<File>();
        try {
            for (String path : paths) {
                InputStream is = new URL("ftp://ftp.ncbi.nih.gov/genomes/Bacteria/" + path).openStream();
                File tempFile = File.createTempFile("ncbi_", ".gbk", dir);
                files.add(tempFile);
                OutputStream os = new FileOutputStream(tempFile);
                copy(is, os);
                os.close();
                is.close();
            }
            ArrayList vars = (ArrayList) GbkUploader.uploadGbk(files, getWsUrl(), ws, id, token);
            GbkUploader.uploadtoWS((ObjectStorage)vars.get(0), ws, id, token, (Genome)vars.get(4), (String) vars.get(5), (ContigSet) vars.get(6), (Map<String, String>)vars.get(7));

            //GbkUploader.uploadtoWS(wc, ws, id, token, genome, contigId, contigSet, meta);

        } finally {
            for (File f : files)
                if (f.exists())
                    f.delete();
        }
    }

    public static long copy(InputStream from, OutputStream to) throws IOException {
        byte[] buf = new byte[10000];
        long total = 0;
        while (true) {
            int r = from.read(buf);
            if (r == -1) {
                break;
            }
            to.write(buf, 0, r);
            total += r;
        }
        return total;
    }

    public static WorkspaceClient createWsClient(String token, String wsUrl) throws Exception {
        WorkspaceClient ret = new WorkspaceClient(new URL(wsUrl), new AuthToken(token));
        ret.setAuthAllowedForHttp(true);
        return ret;
    }

    public static WorkspaceClient createWsClient(String token) throws Exception {
        String wsUrl = getWsUrl();
        return createWsClient(token, wsUrl);
    }

    public static void main(String[] args) throws Exception {
        int port = 18888;
        if (args.length == 1)
            port = Integer.parseInt(args[0]);
        Server jettyServer = new Server(port);
        ServletContextHandler context = new ServletContextHandler(ServletContextHandler.SESSIONS);
        context.setContextPath("/");
        jettyServer.setHandler(context);
        context.addServlet(new ServletHolder(new ContigSetUploadServlet()), "/uploader");
        jettyServer.start();
        jettyServer.join();
    }
}
