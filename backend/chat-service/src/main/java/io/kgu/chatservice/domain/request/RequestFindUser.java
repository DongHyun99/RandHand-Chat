package io.kgu.chatservice.domain.request;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class RequestFindUser {

    @NotNull(message = "OAuth2 인증 서버가 존재하지 않습니다!")
    private String auth;

    @NotNull(message = "이메일이 존재하지 않습니다!")
    @Size(min = 2, message = "이메일은 최소 2자 이상이어야 합니다.")
    @Email
    private String email;

}