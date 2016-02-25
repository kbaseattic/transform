package us.kbase.kbaseenigmametals;

import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import us.kbase.auth.AuthToken;
import us.kbase.auth.TokenFormatException;
//import us.kbase.cmonkey.CmonkeyServerConfig;
import us.kbase.common.service.JsonClientException;
import us.kbase.common.service.Tuple11;
import us.kbase.common.service.UObject;
import us.kbase.common.service.UnauthorizedException;
import us.kbase.workspace.ObjectData;
import us.kbase.workspace.ObjectIdentity;
import us.kbase.workspace.ObjectSaveData;
import us.kbase.workspace.SaveObjectsParams;
import us.kbase.workspace.WorkspaceClient;

public class WsDeluxeUtil {
	private static WorkspaceClient _wsClient = null;
	private static String _token = null;
	private static final String WS_SERVICE_URL = "https://ci.kbase.us/services/ws";//CmonkeyServerConfig.getWsUrl();//"https://kbase.us/services/ws";//
	
	public static WorkspaceClient wsClient(String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException {
		if((_wsClient == null)||(_token == null)||(!token.equals(_token))||(wsServiceUrl != WS_SERVICE_URL)){
			_token = token;
			if (wsServiceUrl == null) {
				_wsClient = new WorkspaceClient(new URL (WS_SERVICE_URL), new AuthToken(token));
			} else {
				_wsClient = new WorkspaceClient(new URL (wsServiceUrl), new AuthToken(token));
			}
			_wsClient.setAuthAllowedForHttp(true);
		}
		return _wsClient;
	} 
	
	public static List<ObjectData> getObjectsFromWorkspace(String workspaceName,
			List<String> names, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {
			List<ObjectIdentity> objectsIdentity = new ArrayList<ObjectIdentity>();
			for (String name : names){
				System.out.println(name);
			ObjectIdentity objectIdentity = new ObjectIdentity().withWorkspace(workspaceName).withName(name);
			objectsIdentity.add(objectIdentity);
			}
			List<ObjectData> returnVal = wsClient(wsServiceUrl, token.toString()).getObjects(
					objectsIdentity);

			return returnVal;
	}

	public static List<ObjectData> getObjectsFromWsByRef(
			List<String> refs, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {
			List<ObjectIdentity> objectsIdentity = new ArrayList<ObjectIdentity>();
			for (String ref : refs){
				System.out.println(ref);
			ObjectIdentity objectIdentity = new ObjectIdentity().withRef(ref);
			objectsIdentity.add(objectIdentity);
			}
			List<ObjectData> returnVal = wsClient(wsServiceUrl, token.toString()).getObjects(
					objectsIdentity);
			return returnVal;
	}

	
	public static ObjectData getObjectFromWorkspace(String workspaceName,
			String name, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {
			List<ObjectIdentity> objectsIdentity = new ArrayList<ObjectIdentity>();
			ObjectIdentity objectIdentity = new ObjectIdentity().withName(name)
					.withWorkspace(workspaceName);
			objectsIdentity.add(objectIdentity);
			List<ObjectData> output = wsClient(wsServiceUrl, token.toString()).getObjects(
					objectsIdentity);

			return output.get(0);
	}

	public static ObjectData getObjectFromWsByRef(String ref, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {
			List<ObjectIdentity> objectsIdentity = new ArrayList<ObjectIdentity>();
			ObjectIdentity objectIdentity = new ObjectIdentity().withRef(ref);
			objectsIdentity.add(objectIdentity);
			List<ObjectData> output = wsClient(wsServiceUrl, token.toString()).getObjects(
					objectsIdentity);

			return output.get(0);
	}

	public static void saveObjectToWorkspace(UObject object, String type,
			String workspaceName, String name, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {

		SaveObjectsParams params = new SaveObjectsParams();
		params.setWorkspace(workspaceName);

		ObjectSaveData objectToSave = new ObjectSaveData();
		objectToSave.setData(object);
		objectToSave.setName(name);
		objectToSave.setType(type);
		Map<String, String> metadata = new HashMap<String, String>();
		objectToSave.setMeta(metadata);
		List<ObjectSaveData> objectsData = new ArrayList<ObjectSaveData>();
		objectsData.add(objectToSave);
		params.setObjects(objectsData);

		List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> ret = null;
			ret = wsClient(wsServiceUrl, token).saveObjects(params);

		System.out.println("Saving object:");
		System.out.println(ret.get(0).getE1());
		System.out.println(ret.get(0).getE2());
		System.out.println(ret.get(0).getE3());
		System.out.println(ret.get(0).getE4());
		System.out.println(ret.get(0).getE5());
		System.out.println(ret.get(0).getE6());
		System.out.println(ret.get(0).getE7());
		System.out.println(ret.get(0).getE8());
		System.out.println(ret.get(0).getE9());
		System.out.println(ret.get(0).getE10());
		System.out.println(ret.get(0).getE11());

	}

	public static void saveObjectToWorkspaceRef(UObject object, String type,
			Long workspaceId, String name, String wsServiceUrl, String token) throws TokenFormatException, UnauthorizedException, IOException, JsonClientException {

		SaveObjectsParams params = new SaveObjectsParams();
		params.setId(workspaceId);

		ObjectSaveData objectToSave = new ObjectSaveData();
		objectToSave.setData(object);
		objectToSave.setName(name);
		objectToSave.setType(type);
		Map<String, String> metadata = new HashMap<String, String>();
		objectToSave.setMeta(metadata);
		List<ObjectSaveData> objectsData = new ArrayList<ObjectSaveData>();
		objectsData.add(objectToSave);
		params.setObjects(objectsData);

		List<Tuple11<Long, String, String, String, Long, String, Long, String, String, Long, Map<String, String>>> ret = null;
			ret = wsClient(wsServiceUrl, token).saveObjects(params);

		System.out.println("Saving object:");
		System.out.println(ret.get(0).getE1());
		System.out.println(ret.get(0).getE2());
		System.out.println(ret.get(0).getE3());
		System.out.println(ret.get(0).getE4());
		System.out.println(ret.get(0).getE5());
		System.out.println(ret.get(0).getE6());
		System.out.println(ret.get(0).getE7());
		System.out.println(ret.get(0).getE8());
		System.out.println(ret.get(0).getE9());
		System.out.println(ret.get(0).getE10());
		System.out.println(ret.get(0).getE11());

	}

}
